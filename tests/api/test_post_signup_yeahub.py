import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import SignUpResponse

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
            response = api_manager.auth_api.register_user(test_user).json()
            response_data = SignUpResponse.model_validate(response)
            token = response_data.access_token

        with allure.step("Проверяем наличие токена в ответе"):
            assert token, "Токен доступа отсутствует в ответе"

        with allure.step("Проверяем наличие юзера в ответе"):
            assert response_data.user is not None, "Данные пользователя отсутствуют в ответе"

        with allure.step(
            "Проверяем что имя юзера в ответе совпадает с именем сгенерированного юзера"
        ):
            assert response_data.user.username == test_user["username"], (
                "username в ответе не совпадает с сгенерированным пользователем"
            )

        with allure.step(
            "Проверяем что 'Email' юзера в ответе совпадает с 'Email' сгенерированного юзера"
        ):
            assert response_data.user.email == test_user["email"], (
                "email в ответе не совпадает с сгенерированным пользователем"
            )
