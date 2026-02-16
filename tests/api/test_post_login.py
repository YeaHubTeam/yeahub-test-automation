from api.api_manager import ApiManager
import pytest
import allure


@allure.epic('Тест - Логин пользователя')
@pytest.mark.api
@pytest.mark.smoke
class TestLoginYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar Odinaev")
    @allure.title('Тестирование логирования пользователя')
    def test_logging_user(self, api_manager: ApiManager, test_user):
        with allure.step('Отправляем Post запрос на создание тестового юзера'):
            response = api_manager.auth_api.register_user(user_data=test_user)

        with allure.step('Логинимся с данными зарегистрированного пользователя'):
            login_data = {
                "username": test_user['email'],
                "password": test_user['password']
            }
            response = api_manager.auth_api.login_user(login_data)
            response_data = response.json()
            token = response_data.get("access_token")

        with allure.step('Проверяем что токен присутствует в ответе'):
            assert token, "Токен доступа отсутствует в ответе"

        with allure.step('Проверяем что токен не пустой'):
            assert len(token) > 0, "Токен не должен быть пустым"

        with allure.step('Проверяем что данные пользователя присутствуют в ответе'):
            assert "user" in response_data, "Данные пользователя отсутствуют в ответе"
            if "email" in response_data["user"]:
                assert response_data["user"]["email"] == test_user["email"], (
                    "Email не совпадает"
                )
            assert "id" in response_data["user"], "ID пользователя отсутствует"
            assert "userRoles" in response_data["user"], "Роли пользователя отсутствуют"
