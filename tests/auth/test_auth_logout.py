import allure
import pytest

from api.api_manager import ApiManager


@allure.epic("Тест - Выхода пользователя из системы")
@pytest.mark.api
@pytest.mark.smoke
class TestLogoutYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Nikolay_Martoplyas")
    @allure.title("Тестирование смены пароля пользователя")
    def test_get_auth_logout_positive(self, api_manager: ApiManager, logged_in_user):
        with allure.step("Отправляем GET запрос на выход пользователя из системы"):
            response = api_manager.auth_api.logout(logged_in_user)
        with allure.step("Проверяем, успешность ответа статус кода = 200"):
            assert response.status_code == 200
