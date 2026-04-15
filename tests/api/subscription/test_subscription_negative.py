import random
import allure
import pytest

from utils.helpers import DataUtils
from constants.constants import NAME_SUBSCRIPTIONS
from models.Subscriptions.model_user_subsriptions import ModelErrorResponse

@pytest.mark.negative
@pytest.mark.api
@allure.label("AQA_Engineer", "Nikolay Martoplyas")
@allure.epic("Тестирование подписки Корнер-кейс")
@allure.feature("Негативные сценарии с неподтвержденным пользоваителем")
class TestSubscriptionNegative:

    @allure.title("Создание подписки с ожиданием на оплату неподтвержденным email")
    def test_creating_subscription_with_unverified_email(self, logged_in_user, api_manager, get_list_subscriptions):
        with allure.step("Получаем ID подписки"):
            id_subscriptions = DataUtils.find_item(
                items=get_list_subscriptions,
                condition= lambda sub: sub.name == NAME_SUBSCRIPTIONS,
                transform= lambda sub: sub.id
            )

        with allure.step("Запрос на формирование оплаты"):
            response = api_manager.subscriptions_api.subscriptions_payment_pending(id_subscriptions, expected_status=403).json()

        with allure.step("Валидация ответа"):
            validate_response = ModelErrorResponse.model_validate(response)

        with allure.step("Assert"):
            assert validate_response.description == "Route is available for verified users!", "Описание не совпадает"

    @allure.title("Удаление подпискии неподтвержденным пользователем")
    def test_delete_subscription_unverified_user(self, logged_in_user, api_manager, get_list_subscriptions):
        with allure.step("Получаем ID подписки и создаем тело запроса"):
            id_subscriptions = DataUtils.find_item(
                items=get_list_subscriptions,
                condition= lambda sub: sub.name == NAME_SUBSCRIPTIONS,
                transform= lambda sub: sub.id
            )

            request_body = {
                "subscriptionId": id_subscriptions,
                "userId": logged_in_user["id"],
                "orderId": "string"
            }
        with allure.step("Запрос на удаление подписки"):
            response = api_manager.subscriptions_api.delete_subscriptions(request_body, expected_status=403).json()

        with allure.step("Валидация ответа"):
            validate_response = ModelErrorResponse.model_validate(response)

        with allure.step("Assert"):
            assert validate_response.description == "Route is available for verified users!", "Описание не совпадает"

    @allure.title("Удаление несущевствующей подписки")
    def test_delete_non_existent_subscription(self, static_user, api_manager):
        request_body = {
            "subscriptionId": random.randint(10, 20),
            "userId": static_user.id,
            "orderId": "string"
        }

        with allure.step("Запрос на удаление подписки"):
            response = api_manager.subscriptions_api.delete_subscriptions(request_body, expected_status=404).json()

        with allure.step("Валидация ответа"):
            validate_response = ModelErrorResponse.model_validate(response)

        with allure.step("Assert"):
            assert validate_response.description == "Subscription not found", "Описание не совпадает"

