# TODO static_user является захардкоженным пользователем с уже подтвержденным email
# TODO измениить эту или переделать другую фикстуру когда будет сделан почтовый клиент
import pytest

from models.Subscriptions.model_subscription import ModelSubscriptionResponse
from models.auth_model import AuthModel
from resources.user_creds import VerifiedUserCreds
from utils.helpers import DataUtils


@pytest.fixture(scope="package")
def static_user(api_manager):
    login_data = {
        "username": VerifiedUserCreds.EMAIL,
        "password": VerifiedUserCreds.PASSWORD
    }
    data_user = api_manager.auth_api.login_user(login_data).json()
    api_manager.auth_api.authenticate(
        (VerifiedUserCreds.EMAIL, VerifiedUserCreds.PASSWORD)
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

