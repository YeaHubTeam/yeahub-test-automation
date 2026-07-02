from typing import Any

import pytest
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.api_manager import ApiManager
from models.Subscriptions.model_subscription import ModelSubscriptionResponse
from tests.mail.signup_retry import (
    authenticate_with_retries,
    register_user_with_retries,
    request_with_integration_retries,
)
from tests.mail.verification_flow import (
    assert_profile_not_verified,
    authenticate_for_teardown,
)
from tests.mail.verified_user import provision_verified_mail_user, yield_payment_link_subscriptions
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
        auth_result = authenticate_for_teardown(api_manager, email, pwd)
        if auth_result == "auth_failed":
            continue
        if auth_result == "transient_failed":
            continue
        delete_resp = api_manager.user_api.delete_user(user_id, expected_status=[200, 204, 404])
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

    def _refresh_identity(_attempt: int, _response) -> None:
        test_user["email"] = DataGenerator.random_email()
        test_user["username"] = DataGenerator.random_username()

    last_response = register_user_with_retries(api_manager, test_user, on_retry=_refresh_identity)
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
def unverified_mail_registered_user(api_manager, test_user):
    """API signUp на MAIL_EMAIL+tag, isVerified=false. Для UI ТК 422 (IMAP verify)."""
    require_mail_creds()
    mail_identity = {"started_at": None}
    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()
    mail_identity["started_at"] = started_at
    test_user["email"] = recipient_email
    test_user["password"] = password
    test_user["username"] = username

    def _refresh_mail_identity(_attempt: int, _response) -> None:
        new_started_at, _new_tag, new_email, new_password, new_username = new_plus_tagged_email()
        mail_identity["started_at"] = new_started_at
        test_user["email"] = new_email
        test_user["password"] = new_password
        test_user["username"] = new_username

    last_response = register_user_with_retries(
        api_manager, test_user, on_retry=_refresh_mail_identity
    )
    assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

    test_user["id"] = last_response.json().get("user", {}).get("id")
    test_user["token"] = last_response.json().get("access_token")
    test_user["mail_since"] = mail_identity["started_at"]
    assert_profile_not_verified(api_manager, test_user["email"], test_user["password"])
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
    mail_identity: dict[str, Any] = {"started_at": None}

    def _refresh_mail_identity(_attempt: int, _response) -> None:
        new_started_at, _new_tag, new_email, new_password, new_username = new_plus_tagged_email()
        mail_identity["started_at"] = new_started_at
        test_user["email"] = new_email
        test_user["password"] = new_password
        test_user["username"] = new_username

    provision_verified_mail_user(
        api_manager,
        user_payload=test_user,
        mail_state=mail_identity,
        on_signup_retry=_refresh_mail_identity,
    )
    yield test_user
    _delete_user_try_passwords(
        api_manager,
        email=test_user["email"],
        user_id=test_user.get("id"),
        password=test_user["password"],
        active_password=test_user.get("active_password"),
    )


@pytest.fixture(scope="module")
def verified_subscription_user(api_manager):
    """Verified user per API subscription module (signUp → IMAP verify → delete)."""
    user = provision_verified_mail_user(api_manager)
    yield user
    _delete_user_try_passwords(
        api_manager,
        email=user["email"],
        user_id=user.get("id"),
        password=user["password"],
        active_password=user.get("active_password"),
    )


@pytest.fixture
def logged_in_user(api_manager, registered_user):
    """Авторизация пользователя"""
    authenticate_with_retries(api_manager, registered_user["email"], registered_user["password"])

    return registered_user


@pytest.fixture(scope="session")
def get_list_subscriptions(api_manager):
    last_response = request_with_integration_retries(
        lambda: api_manager.subscriptions_api.get_subscriptions(expected_status=[200, 503]),
    )
    assert last_response.status_code == 200, "subscriptions list is unavailable (503) after retries"

    response_json = last_response.json()
    return DataUtils.type_adapter(list[ModelSubscriptionResponse], response_json)


@pytest.fixture(scope="function")
def payment_link_subscriptions(api_manager, verified_subscription_user, get_list_subscriptions):
    """Создает ссылку на оплату подписки (API tests: module-scoped verified user)."""
    yield from yield_payment_link_subscriptions(
        api_manager,
        user=verified_subscription_user,
        subscriptions_catalog=get_list_subscriptions,
    )
