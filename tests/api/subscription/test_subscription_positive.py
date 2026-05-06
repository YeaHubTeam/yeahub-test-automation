import datetime
from typing import List
from urllib.parse import urlparse

import allure
import pytest
import requests
from pydantic import TypeAdapter
from pytest_check import check

from constants.constants import NAME_SUBSCRIPTIONS, PAYMENT_SUBSCRIPTIONS_URL
from constants.currency_code import CurrencyCode
from models.Subscriptions.model_data_payment import DataPaymentModel
from models.Subscriptions.model_user_subsriptions import (
    ModelErrorResponse,
    UserSubscriptionResponse,
)
from payloads.subscription_rates import TarifList
from utils.helpers import DataUtils

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression]


@pytest.mark.api
@allure.label("AQA_Engineer", "Nikolay Martoplyas")
@allure.epic("Тестирование подписки Хэппи-пасс")
@allure.feature(
    "Получение подписок у пользователя, "
    "создание подписки с ожиданием оплаты, "
    "удаление подписки, "
    "добавление пробной подписки"
)
class TestSubscriptionPositive:
    @pytest.mark.smoke
    @allure.title("Создание подписки с ожиданием оплаты")
    def test_subscription_pyments(self, payment_link_subscriptions):
        with allure.step("Разбиваем url на части"):
            result = urlparse(payment_link_subscriptions)

        with allure.step("Assert"):
            """
            result.scheme - проверяет что URL имеет протокол
            result.netloc - проверяет наличие домена
            """
            assert all([result.scheme, result.netloc]), (
                f"Строка {payment_link_subscriptions} не является ссылкой"
            )

    @allure.title("Проверка данных для оплаты")
    def test_payment_details(self, payment_link_subscriptions, static_user):
        with allure.step("Берем финальную цену подписки из документации в копейках"):
            price_tarif = DataUtils.find_item(
                items=TarifList.base_tarif().tarifs,
                condition=lambda tarif: tarif.name == NAME_SUBSCRIPTIONS,
                transform=lambda tarif: int(tarif.finalPrice) * 100,
            )

        with allure.step("Извлечение уникального ID для оплаты"):
            payment_id = payment_link_subscriptions.split("/")[-1]

        with allure.step("Извлечение данных для оплаты"):
            payment_data = requests.get(f"{PAYMENT_SUBSCRIPTIONS_URL}{payment_id}").json()

        with allure.step("Проверка дынных для оплаты через модель пудантик"):
            payment_details = DataPaymentModel.model_validate(payment_data)

        with allure.step("Assert"):
            check.equal(payment_details.sessionId, payment_id, "ID сессии не совпадают")
            check.equal(payment_details.status.value, "NEW", "Статус не совпадает")
            check.equal(payment_details.merchant.name, "YeaHub", "Название не совпадает")
            check.equal(payment_details.merchant.backUrl, "https://yeahub.ru", "URL не совпадает")
            check.equal(
                payment_details.templateParams.merchantPhone,
                "9183374202",
                "Номер телефона не совпадает",
            )
            check.equal(
                payment_details.templateParams.companyName,
                "ИП КУЯНЕЦ РУСЛАН РОСТИСЛАВОВИЧ",
                "Получатель не совпадает",
            )
            check.equal(
                payment_details.templateParams.companyAddress,
                "ул им. генерала И.Л. Шифрина, д 1",
                "Получатель не совпадает",
            )
            check.equal(payment_details.amount, price_tarif, "Итоговая сумма не совпадает")
            check.equal(payment_details.currency, CurrencyCode.RUB, "Код валюты не совпадает")
            check.equal(
                payment_details.order.description,
                "Оплата подписки 'Премиум на 3 месяца'",
                "Описание не совпадает",
            )
            check.equal(payment_details.customer.key, static_user.id, "ID заказчика не совпадают")
            check.equal(
                payment_details.customer.email, static_user.email, "Email заказчика не совпадают"
            )
            assert datetime.datetime.fromisoformat(payment_details.status.timestamp), (
                "Неверный формат даты"
            )

    @allure.title("Проверка статуса подписки после создания оплаты")
    def test_status_subscription_after_payment(
        self, payment_link_subscriptions, api_manager, static_user
    ):
        with allure.step("Извлекаем конкретную подписку у пользователя"):
            response = api_manager.subscriptions_api.get_subscriptions_users(static_user.id).json()

        with allure.step("Валидируем данные через пудантик"):
            validate_response = DataUtils.type_adapter(List[UserSubscriptionResponse], response)

        with allure.step("Выибираем нужную подписку из списка"):
            subscription = DataUtils.find_item(
                items=validate_response,
                condition=lambda sub: sub.subscription.name == NAME_SUBSCRIPTIONS,
                transform=lambda sub: sub.state,
            )

        with allure.step("Assert"):
            assert subscription == "pending_payment", "Статус подписки не верный"

    @pytest.mark.smoke
    @allure.title("Удаление подписки ")
    def test_delete_subscription(self, static_user, api_manager, payment_link_subscriptions):
        with allure.step("Получаем список подписок у пользователя"):
            response = api_manager.subscriptions_api.get_subscriptions_users(static_user.id).json()

        with allure.step("Валидируем данные через пудантик"):
            validate_response = DataUtils.type_adapter(List[UserSubscriptionResponse], response)

        with allure.step("Выибираем нужную подписку из списка"):
            user_subscription = DataUtils.find_item(
                items=validate_response,
                condition=lambda sub: sub.state == "pending_payment",
            )

        with allure.step("Удаление подписки "):
            request_body = {
                "subscriptionId": user_subscription.subscription_id,
                "userId": static_user.id,
                "orderId": user_subscription.id,
            }
            api_manager.subscriptions_api.delete_subscriptions(request_body)

        with allure.step("Получаем обновленный список подписок после удаления"):
            updated_subscriptions = api_manager.subscriptions_api.get_subscriptions_users(
                static_user.id
            ).json()

        with allure.step("Валидируем Обновленные данные через пудантик"):
            validate_updated = DataUtils.type_adapter(
                List[UserSubscriptionResponse], updated_subscriptions
            )

        with allure.step("Проверяем изменение статуса"):
            subscription_state = DataUtils.find_item(
                items=validate_updated,
                condition=lambda sub: sub.subscription.name == NAME_SUBSCRIPTIONS,
                transform=lambda sub: sub.state,
            )

        with allure.step("Assert"):
            assert subscription_state == "canceled", "Статус не совпадает"

    @pytest.mark.smoke
    @allure.title("Создание заказа на оплату с бесплатной подпиской")
    def test_free_subscription(self, api_manager, static_user, get_list_subscriptions):
        with allure.step("Получаем ID бесплатной подписки"):
            subscription_id = DataUtils.find_item(
                items=get_list_subscriptions,
                condition=lambda sub: sub.code == "free",
                transform=lambda sub: sub.id,
            )

        with allure.step("Делаем запрос на создание оплаты с беcплатной подпиской"):
            response = api_manager.subscriptions_api.subscriptions_payment_pending(
                subscription_id, expected_status=400
            ).json()

        with allure.step("Валидация ответа"):
            validate_response = ModelErrorResponse.model_validate(response)

        with allure.step("Assert"):
            assert (
                "Неверная сумма. Сумма должна быть больше или равна 100 копеек."
                in validate_response.description
            ), "Описание отсутствует"

    @allure.title("Повторный запрос на оплату подписки")
    def test_retry_subscription_payment(
        self, static_user, api_manager, get_list_subscriptions, payment_link_subscriptions
    ):
        with allure.step("Получаем ID подписки"):
            subscription_id = DataUtils.find_item(
                items=get_list_subscriptions,
                condition=lambda sub: sub.name == NAME_SUBSCRIPTIONS,
                transform=lambda sub: sub.id,
            )
        with allure.step("Делаем повторный запрос на создание ссылки на оплату"):
            response = api_manager.subscriptions_api.subscriptions_payment_pending(
                subscription_id, static_user.email
            ).text

        with allure.step("Assert"):
            assert response == payment_link_subscriptions
