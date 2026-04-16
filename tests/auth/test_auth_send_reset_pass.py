import pytest

from api.api_manager import ApiManager

# TODO ТЕСТ ТРЕБУЕТ ДОРАБОТКИ! НЕ ГОТОВО! Жду таск - https://tracker.yandex.ru/YH-1756


@pytest.mark.skip(reason="Нужен мейлер клиент - Ждем таск: https://tracker.yandex.ru/YH-1756")
class TestSendResetPassYeahub:
    def test_get_auth_send_reset_pass_positive(self, api_manager: ApiManager, logged_in_user):
        response = api_manager.auth_api.send_reset_pass(logged_in_user)
