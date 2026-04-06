from api.api_manager import ApiManager
from models.user_response_model import CreatedUserResponse
import pytest
import allure


@allure.epic("Тест - Регистрация пользователя")
@pytest.mark.api
@pytest.mark.smoke
class TestSignUpYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar Odinaev")
    @allure.title("Тестирование регистрации пользователя")
    def test_signup_user(self, api_manager: ApiManager, test_user):
        with allure.step("Оправляем POST запрос с данными тестового пользователя"):
            response = api_manager.auth_api.register_user(test_user).json()
            response_model = CreatedUserResponse(**response)

        with allure.step("Проверяем наличие токена в ответе"):
            assert "access_token" in response_model, "Access token missing"

        with allure.step("Проверяем наличие юзера в ответе"):
            assert "user" in response_model, "User data missing"

        with allure.step(
            "Проверяем что имя юзера в ответе совпадает с именем сгенерированного юзера"
        ):
            assert response_model["user"]["username"] == test_user["username"]

        with allure.step(
            "Проверяем что 'Email' юзера в ответе совпадает с 'Email' сгенерированного юзера"
        ):
            assert response_model["user"]["email"] == test_user["email"]
