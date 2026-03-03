from api.api_manager import ApiManager
import allure
import pytest


@allure.epic('Тест - Смены пароля')
@pytest.mark.api
@pytest.mark.smoke
class TestPasswordChangeYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Nikolay_Martoplyas")
    @allure.title('Тестирование смены пароля пользователя')
    def test_user_can_change_password_successfully(self, api_manager: ApiManager, logged_in_user):
        with allure.step('Оправляем PATCH запрос с данными нового пароля пользователя'):
            response = api_manager.auth_api.password_change(logged_in_user)
        with allure.step('Проверяем, что статус ответ успешный.'):
            assert response.status_code == 200
