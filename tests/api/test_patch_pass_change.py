import allure
import pytest

from api.api_manager import ApiManager
from payloads.auth_payloads import AuthPayloads

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression]


@allure.epic("Тест - Смены пароля")
@pytest.mark.api
@pytest.mark.smoke
class TestPasswordChangeYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Nikolay_Martoplyas")
    @allure.title("Тестирование смены пароля пользователя")
    def test_user_can_change_password_successfully(self, api_manager: ApiManager, logged_in_user):
        with allure.step("Отправляем PATCH запрос с данными нового пароля пользователя"):
            payload = AuthPayloads.payload_password()
            response = api_manager.auth_api.password_change(logged_in_user["id"], payload)
        with allure.step("Проверяем, что статус ответ успешный."):
            assert response.status_code == 200
            assert response.json().get("access_token"), "Токен не найден в ответе на смену пароля"
