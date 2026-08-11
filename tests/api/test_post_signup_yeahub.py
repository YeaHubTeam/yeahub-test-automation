import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import SignUpResponse
from utils.retry import request_with_retries

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression, pytest.mark.pr_safe]


@allure.epic("Тест - Регистрация пользователя")
@pytest.mark.api
@pytest.mark.smoke
class TestSignUpYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar Odinaev")
    @allure.title("Тестирование регистрации пользователя")
    def test_signup_user(self, api_manager: ApiManager, test_user):
        with allure.step("Отправляем POST-запрос с данными тестового пользователя"):
            last_response = request_with_retries(
                lambda: api_manager.auth_api.register_user(test_user, expected_status=[201, 503]),
                success_status=201,
            )
            assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

            response_data = SignUpResponse.model_validate(last_response.json())
            token = response_data.access_token

        with allure.step("Проверяем наличие токена в ответе"):
            assert token, "Токен доступа отсутствует в ответе"

        with allure.step("Проверяем наличие юзера в ответе"):
            assert response_data.user is not None, "Данные пользователя отсутствуют в ответе"

        with allure.step(
            "Проверяем что имя юзера в ответе совпадает с именем сгенерированного юзера"
        ):
            assert response_data.user.username == test_user["username"]

        with allure.step(
            "Проверяем что 'Email' юзера в ответе совпадает с 'Email' сгенерированного юзера"
        ):
            assert response_data.user.email == test_user["email"]
