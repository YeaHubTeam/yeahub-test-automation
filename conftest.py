import pytest
import requests
from api.api_manager import ApiManager
from utils.data_generator import DataGenerator
from utils.helpers import DataUtils
from models.Subscriptions.model_subscription import ModelSubscriptionResponse
from models.auth_model import AuthModel
from pydantic import TypeAdapter


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

# TODO static_user является захардкоженным пользователем с уже подтвержденным email
# TODO измениить эту или переделать другую фикстуру когда будет сделан почтовый клиент
@pytest.fixture(scope="package")
def static_user(api_manager):
    login_data = {
        "username": "kolyan94martoplyas@gmail.com",
        "password": "111!qqqQ"
    }
    data_user = api_manager.auth_api.login_user(login_data).json()
    api_manager.auth_api.authenticate(
        ("kolyan94martoplyas@gmail.com", "111!qqqQ")
    )
    validate_user = AuthModel.model_validate(data_user)
    yield validate_user.user
    api_manager.auth_api.logout()

@pytest.fixture(scope="session")
def get_list_subscriptions(api_manager):
    response = api_manager.subscriptions_api.get_subscriptions().json()
    validate_response = DataUtils.type_adapter(list[ModelSubscriptionResponse], response)
    return validate_response

@pytest.fixture(scope="function")
def payment_link_subscriptions(api_manager, static_user, get_list_subscriptions):
    """Создает ссылку на оплату подписки"""
    id_subscriptions = DataUtils.find_item(
        items=get_list_subscriptions,
        condition= lambda sub: sub.name == "Премиум на 3 месяца",
        transform= lambda sub: sub.id
    )
    response = api_manager.subscriptions_api.subscriptions_payment_pending(id_subscriptions, static_user["email"])
    payment_url = response.text
    yield payment_url
    request_body = {
        "subscriptionId": id_subscriptions,
        "userId": static_user.id,
        "orderId": "string"
    }
    api_manager.subscriptions_api.delete_subscriptions(request_body)

