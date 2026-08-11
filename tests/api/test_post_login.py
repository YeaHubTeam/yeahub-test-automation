import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import LoginResponse
from utils.retry import request_with_retries

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
            last_signup = request_with_retries(
                lambda: api_manager.auth_api.register_user(test_user, expected_status=[201, 503]),
                success_status=201,
            )
            assert last_signup is not None
            assert last_signup.status_code == 201, "signUp is unavailable (503) after retries"

        with allure.step("Логинимся с данными зарегистрированного пользователя"):
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"],
            }
            last_login = request_with_retries(
                lambda: api_manager.auth_api.login_user(login_data, expected_status=[201, 503]),
                success_status=201,
            )
            assert last_login is not None
            assert last_login.status_code == 201, "login is unavailable (503) after retries"

            response_data = LoginResponse.model_validate(last_login.json())
            token = response_data.access_token

        with allure.step("Проверяем что токен присутствует в ответе"):
            assert token, "Токен доступа отсутствует в ответе"

        with allure.step("Проверяем что данные пользователя присутствуют в ответе"):
            assert response_data.user is not None, "Данные пользователя отсутствуют в ответе"
            assert response_data.user.email == test_user["email"], "Email не совпадает"
            assert response_data.user.id, "ID пользователя отсутствует"
            assert response_data.user.userRoles is not None, "Роли пользователя отсутствуют"
