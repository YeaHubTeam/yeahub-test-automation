import allure
import pytest
from payloads.subscription_rates import TarifList
from utils.helpers import DataUtils


@pytest.mark.smoke
@pytest.mark.api
@allure.label("AQA_Engineer", "Nikolay Martoplyas")
@allure.epic("Тестирование полей подписок")
@allure.feature("Получение списка подписок, и проверка полей в каждой подписке")
class TestSubscriptionValidation:

    @pytest.mark.xfail(reason="По документации должно быть 5 пдписок сервер возвращает 6")
    @allure.title("Получение списка подписок")
    def test_get_list_subscriptions(self, static_user, api_manager):
        with allure.step("Запрос на получение списка подписок"):
            response = api_manager.subscriptions_api.get_subscriptions().json()

        with allure.step("Assert"):
            assert len(response) == 5, "Колличевсто словарей не совпадает"

    @allure.title("Параметризированный тест, проверка соответсвия полей в тарифах")
    @pytest.mark.parametrize("expected", TarifList.base_tarif().tarifs,
                             ids=[i.name for i in TarifList.base_tarif().tarifs])
    def test_subscriptions_tariff_candidate(self, get_list_subscriptions, expected):
        with allure.step("Получение тарифа который соответсвует в очереди expected"):
            actual_subscriptions = DataUtils.find_item(
                items=get_list_subscriptions,
                condition= lambda item: item.name == expected.name
            )

        with allure.step("Assert"):
            assert actual_subscriptions == expected, f"Ожидали {expected}, а получили {actual_subscriptions}"

