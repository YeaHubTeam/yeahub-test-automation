import time

import pytest
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.api_manager import ApiManager
from models.auth_model import AuthModel
from models.Subscriptions.model_subscription import ModelSubscriptionResponse
from models.Subscriptions.model_user_subsriptions import UserSubscriptionResponse
from resources.user_creds import VerifiedUserCreds
from tests.mail.verification_flow import profile_user_id, verify_api_registered_user_email
from tests.ui.flows.register_mail_interview_flow import new_plus_tagged_email, require_mail_creds
from utils.data_generator import DataGenerator
from utils.helpers import DataUtils

load_dotenv()


def _delete_user_try_passwords(
    api_manager: ApiManager,
    *,
    email: str,
    user_id: str | None,
    password: str,
    active_password: str | None = None,
) -> None:
    """Teardown: login с active_password (если меняли) или исходным паролем → delete_user."""
    if not user_id:
        return
    candidates: list[str] = []
    for pwd in (active_password, password):
        if pwd and pwd not in candidates:
            candidates.append(pwd)
    for pwd in candidates:
        authed = False
        for attempt in range(3):
            try:
                api_manager.auth_api.authenticate((email, pwd))
                authed = True
                break
            except ValueError:
                break
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ) as exc:
                if attempt == 2:
                    raise exc
                time.sleep(1.5 * (attempt + 1))
        if not authed:
            continue
        delete_resp = api_manager.user_api.delete_user(
            user_id, expected_status=[200, 204, 404, 401]
        )
        if delete_resp.status_code in (200, 204, 404):
            return


def _session_with_retries() -> requests.Session:
    """Транспортные ретраи на сетевые ошибки (без ретраев по HTTP-статусам).

    Ретраи по 502/503/504 обрабатываются в `CustomRequester`, чтобы избежать "двойных" ретраев
    (Session Retry + логика клиента), которые раздувают время прогона.
    """
    session = requests.Session()
    retry = Retry(
        total=1,
        connect=1,
        read=1,
        status=0,
        backoff_factor=0.2,
        allowed_methods=frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PUT", "TRACE"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


@pytest.fixture(scope="session")
def session():
    session = _session_with_retries()
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(session)


@pytest.fixture
def test_user():
    return {
        "username": DataGenerator.random_username(),
        "password": DataGenerator.random_password(),
        "email": DataGenerator.random_email(),
        "phone": DataGenerator.random_phone(),
        "country": DataGenerator.random_country(),
        "city": DataGenerator.random_city(),
        "birthday": DataGenerator.random_birthday(),
        "address": DataGenerator.random_address(),
        # Без внешнего URL: бэкенд при delete_user иначе может дергать storage и отвечать
        # storage.image.not_found (faker image_url / placekitten и т.п.).
        "avatarUrl": None,
    }


@pytest.fixture
def registered_user(api_manager, test_user):
    """Регистрация пользователя и удаление его после теста"""
    # signUp иногда отвечает 503 от nginx; для устойчивости делаем короткие ретраи.
    # Важно: на каждом ретрае меняем email/username, чтобы не упираться в 409 duplicate.
    last_response = None
    for attempt in range(5):
        last_response = api_manager.auth_api.register_user(
            test_user, expected_status=[201, 503, 409]
        )
        if last_response.status_code == 201:
            break
        test_user["email"] = DataGenerator.random_email()
        test_user["username"] = DataGenerator.random_username()
        time.sleep(2 * (attempt + 1))

    assert last_response is not None
    assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

    test_user["id"] = last_response.json().get("user", {}).get("id")
    test_user["token"] = last_response.json().get("access_token")
    yield test_user
    _delete_user_try_passwords(
        api_manager,
        email=test_user["email"],
        user_id=test_user.get("id"),
        password=test_user["password"],
        active_password=test_user.get("active_password"),
    )


@pytest.fixture
def verified_registered_user(api_manager, test_user):
    """signUp → IMAP verify → teardown delete. Для mail/UI с `isVerified=true` (не для TC 113).

    Email — `local+tag@domain` на MAIL_EMAIL (иначе IMAP не найдёт письмо верификации).
    """
    require_mail_creds()
    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()
    test_user["email"] = recipient_email
    test_user["password"] = password
    test_user["username"] = username
    last_response = None
    for attempt in range(5):
        last_response = api_manager.auth_api.register_user(
            test_user, expected_status=[201, 503, 409]
        )
        if last_response.status_code == 201:
            break
        started_at, _tag, recipient_email, password, username = new_plus_tagged_email()
        test_user["email"] = recipient_email
        test_user["password"] = password
        test_user["username"] = username
        time.sleep(2 * (attempt + 1))

    assert last_response is not None
    assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

    test_user["id"] = last_response.json().get("user", {}).get("id")
    test_user["token"] = last_response.json().get("access_token")
    api_manager.auth_api.authenticate((test_user["email"], test_user["password"]))
    user_id = profile_user_id(api_manager.auth_api.profile().json())
    verify_api_registered_user_email(
        api_manager,
        email=test_user["email"],
        password=test_user["password"],
        user_id=user_id,
        started_at=started_at,
    )
    yield test_user
    _delete_user_try_passwords(
        api_manager,
        email=test_user["email"],
        user_id=test_user.get("id"),
        password=test_user["password"],
        active_password=test_user.get("active_password"),
    )


@pytest.fixture
def logged_in_user(api_manager, registered_user):
    """Авторизация пользователя"""
    login_data = {
        "username": registered_user["email"],
        "password": registered_user["password"],
    }
    last_login = None
    for attempt in range(5):
        last_login = api_manager.auth_api.login_user(login_data, expected_status=[201, 503])
        if last_login.status_code == 201:
            break
        time.sleep(2 * (attempt + 1))
    assert last_login is not None
    assert last_login.status_code == 201, "login is unavailable (503) after retries"

    api_manager.auth_api.authenticate((registered_user["email"], registered_user["password"]))

    return registered_user


@pytest.fixture(scope="package")
def static_user(api_manager):
    # TODO static_user является захардкоженным пользователем с уже подтвержденным email.
    # TODO изменить эту фикстуру или переделать другую, когда будет сделан почтовый клиент.
    login_data = {
        "username": VerifiedUserCreds.EMAIL,
        "password": VerifiedUserCreds.PASSWORD,
    }
    last_login = None
    for attempt in range(5):
        last_login = api_manager.auth_api.login_user(login_data, expected_status=[201, 503])
        if last_login.status_code == 201:
            break
        time.sleep(2 * (attempt + 1))
    assert last_login is not None
    assert last_login.status_code == 201, "static user login is unavailable (503) after retries"

    data_user = last_login.json()
    api_manager.auth_api.authenticate((VerifiedUserCreds.EMAIL, VerifiedUserCreds.PASSWORD))
    validate_user = AuthModel.model_validate(data_user)
    yield validate_user.user
    api_manager.auth_api.logout(expected_status=[200, 401, 503])


@pytest.fixture(scope="session")
def get_list_subscriptions(api_manager):
    last_response = None
    for attempt in range(5):
        last_response = api_manager.subscriptions_api.get_subscriptions(expected_status=[200, 503])
        if last_response.status_code == 200:
            break
        time.sleep(2 * (attempt + 1))

    assert last_response is not None
    assert last_response.status_code == 200, "subscriptions list is unavailable (503) after retries"

    response_json = last_response.json()
    return DataUtils.type_adapter(list[ModelSubscriptionResponse], response_json)


@pytest.fixture(scope="function")
def payment_link_subscriptions(api_manager, static_user, get_list_subscriptions):
    """Создает ссылку на оплату подписки."""
    id_subscriptions = DataUtils.find_item(
        items=get_list_subscriptions,
        condition=lambda sub: sub.name == "Премиум на 3 месяца",
        transform=lambda sub: sub.id,
    )
    # subscriptions/users иногда отвечает 503 от nginx; для устойчивости делаем короткие ретраи
    last_existing = None
    for attempt in range(5):
        last_existing = api_manager.subscriptions_api.get_subscriptions_users(
            static_user.id, expected_status=[200, 503]
        )
        if last_existing.status_code == 200:
            break
        time.sleep(2 * (attempt + 1))

    assert last_existing is not None
    assert last_existing.status_code == 200, (
        "subscriptions/users is unavailable (503) after retries"
    )

    existing_subscriptions = last_existing.json()
    validated_subscriptions = DataUtils.type_adapter(
        list[UserSubscriptionResponse], existing_subscriptions
    )
    pending_subscription = DataUtils.find_item(
        items=validated_subscriptions,
        condition=lambda sub: (
            sub.subscription_id == id_subscriptions and sub.state in ["pending_payment", "active"]
        ),
    )
    if pending_subscription:
        cleanup_body = {
            "subscriptionId": id_subscriptions,
            "userId": static_user.id,
            "orderId": pending_subscription.id,
        }
        api_manager.subscriptions_api.delete_subscriptions(cleanup_body, expected_status=[200, 404])

    # payment/init иногда отвечает 503 от nginx; для устойчивости делаем короткие ретраи
    last_response = None
    for attempt in range(5):
        last_response = api_manager.subscriptions_api.subscriptions_payment_pending(
            id_subscriptions,
            static_user.email,
            expected_status=[200, 503],
        )
        if last_response.status_code == 200:
            break
        time.sleep(2 * (attempt + 1))

    assert last_response is not None
    assert last_response.status_code == 200, "payment/init is unavailable (503) after retries"

    payment_url = last_response.text
    yield payment_url
    teardown_subscriptions = api_manager.subscriptions_api.get_subscriptions_users(
        static_user.id
    ).json()
    teardown_validated = DataUtils.type_adapter(
        list[UserSubscriptionResponse], teardown_subscriptions
    )
    teardown_row = DataUtils.find_item(
        items=teardown_validated,
        condition=lambda sub: (
            sub.subscription_id == id_subscriptions and sub.state in ["pending_payment", "active"]
        ),
    )
    if teardown_row:
        request_body = {
            "subscriptionId": id_subscriptions,
            "userId": static_user.id,
            "orderId": teardown_row.id,
        }
        api_manager.subscriptions_api.delete_subscriptions(request_body)
