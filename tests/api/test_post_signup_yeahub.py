import allure

from api.api_manager import ApiManager
import pytest


@allure.epic('Тест - Регистрация пользователя')
@pytest.mark.api
@pytest.mark.smoke
class TestSignUpYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar Odinaev")
    @allure.title('Тестирование регистрации пользователя')
    def test_signup_user(self, api_manager: ApiManager, test_user):
        with allure.step('Оправляем POST запрос с данными тестового пользователя'):
            response = api_manager.auth_api.register_user(test_user)
            response_data = response.json()

        with allure.step("Проверяем наличие токена в ответе"):
            assert "access_token" in response_data, "Access token missing"

        with allure.step("Проверяем наличие юзера в ответе"):
            assert "user" in response_data, "User data missing"

        with allure.step("Проверяем что имя юзера в ответе совпадает с именем сгенерированного юзера"):
            assert response_data["user"]["username"] == test_user["username"]

        with allure.step("Проверяем что 'Email' юзера в ответе совпадает с 'Email' сгенерированного юзера"):
            assert response_data["user"]["email"] == test_user["email"]


