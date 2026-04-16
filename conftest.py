import pytest
import requests
from api.api_manager import ApiManager
from utils.data_generator import DataGenerator
from utils.helpers import DataUtils
from models.Subscriptions.model_subscription import ModelSubscriptionResponse
from models.auth_model import AuthModel
from resources.user_creds import VerifiedUserCreds


@pytest.fixture(scope="session")
def session():
    session = requests.Session()
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
        "avatarUrl": DataGenerator.random_avatar_url(),
    }


@pytest.fixture
def registered_user(api_manager, test_user):
    """Регистрация пользователя и удаление его после теста"""
    response = api_manager.auth_api.register_user(test_user, expected_status=201)
    test_user["id"] = response.json().get("user", {}).get("id")
    test_user["token"] = response.json().get("access_token")
    yield test_user
    if (
        "Authorization" not in api_manager.auth_api.headers
    ):  # Проверяем что пользоватпель не залогинен
        # Так как чтоб удалить пользователя нужно залогинется
        api_manager.auth_api.authenticate((test_user["email"], test_user["password"]))
    api_manager.user_api.delete_user(test_user["id"], expected_status=[404, 401])
    # TODO поменять ожидаемый сатус код в teardown в методе "delete_user" на 200 после исправления бага


@pytest.fixture
def logged_in_user(api_manager, registered_user):
    """Авторизация пользователя"""
    login_data = {
        "username": registered_user["email"],
        "password": registered_user["password"],
    }
    api_manager.auth_api.login_user(login_data)
    api_manager.auth_api.authenticate(
        (registered_user["email"], registered_user["password"])
    )

    return registered_user

