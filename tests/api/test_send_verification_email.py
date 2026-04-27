import allure
import pytest

from api.api_manager import ApiManager

# TODO - ТЕСТ ТРЕБУЕТ ДОРАБОТКИ! НЕ ГОТОВО!

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression]


@allure.epic("Тест - Отправка емейла верификации")
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.skip(reason="Нужен мейлер клиент - Ждем таск: https://tracker.yandex.ru/YH-1756")
class TestSendVerificationEmailYeahub:
    def test_send_verification_email(self, api_manager: ApiManager, logged_in_user):
        response = api_manager.auth_api.send_verification_email(logged_in_user)

        assert response.status_code == 200
