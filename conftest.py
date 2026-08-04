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
    request_with_integration_retries,
)
from utils.write_fixtures import create_registered_user, cleanup_user, create_verified_mail_registered_user, create_unverified_mail_registered_user
from tests.mail.verified_user import provision_verified_mail_user, yield_payment_link_subscriptions
from utils.data_generator import DataGenerator
from utils.helpers import DataUtils

load_dotenv()

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
        "username": DataGenerator.unique_username(),
        "password": DataGenerator.random_password(),
        "email": DataGenerator.unique_email(),
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
    test_user = create_registered_user(api_manager, test_user)
    yield test_user
    cleanup_user(api_manager, test_user)


@pytest.fixture
def unverified_mail_registered_user(api_manager, test_user):
    """API signUp на MAIL_EMAIL+tag, isVerified=false. Для UI ТК 422 (IMAP verify)."""
    create_unverified_mail_registered_user(api_manager, test_user)
    yield test_user
    cleanup_user(api_manager, test_user)

@pytest.fixture
def verified_registered_user(api_manager, test_user):
    """signUp → IMAP verify → teardown delete. Для mail/UI с `isVerified=true` (не для TC 113).

    Email — `local+tag@domain` на MAIL_EMAIL (иначе IMAP не найдёт письмо верификации).
    """
    create_verified_mail_registered_user(api_manager, test_user)
    yield test_user
    cleanup_user(api_manager, test_user)

@pytest.fixture(scope="module")
def verified_subscription_user(api_manager):
    """Verified user per API subscription module (signUp → IMAP verify → delete)."""
    user = provision_verified_mail_user(api_manager)
    create_verified_mail_registered_user(api_manager, user)
    yield user
    cleanup_user(api_manager, user)


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
