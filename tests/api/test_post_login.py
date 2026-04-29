import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import LoginResponse

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression, pytest.mark.pr_safe]


@allure.epic("Тест - Логин пользователя")
@pytest.mark.api
@pytest.mark.smoke
class TestLoginYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar Odinaev")
    @allure.title("Тестирование логирования пользователя")
    def test_logging_user(self, api_manager: ApiManager, test_user):
        with allure.step("Отправляем POST-запрос на создание тестового пользователя"):
            api_manager.auth_api.register_user(user_data=test_user)

        with allure.step("Логинимся с данными зарегистрированного пользователя"):
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"],
            }
            response = api_manager.auth_api.login_user(login_data).json()
            response_data = LoginResponse.model_validate(response)
            token = response_data.access_token

        with allure.step("Проверяем что токен присутствует в ответе"):
            assert token, "Токен доступа отсутствует в ответе"

        with allure.step("Проверяем что данные пользователя присутствуют в ответе"):
            assert response_data.user is not None, "Данные пользователя отсутствуют в ответе"
            assert response_data.user.email == test_user["email"], "Email не совпадает"
            assert response_data.user.id, "ID пользователя отсутствует"
            assert response_data.user.userRoles is not None, "Роли пользователя отсутствуют"
