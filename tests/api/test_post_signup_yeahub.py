import time

import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import SignUpResponse
from utils.data_generator import DataGenerator

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
            last_response = None
            for attempt in range(5):
                last_response = api_manager.auth_api.register_user(
                    test_user, expected_status=[201, 503, 409]
                )
                if last_response.status_code == 201:
                    break
                # на ретраях обновляем уникальные поля, чтобы не упереться в 409
                test_user["email"] = DataGenerator.random_email()
                test_user["username"] = DataGenerator.random_username()
                time.sleep(2 * (attempt + 1))

            assert last_response is not None
            assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

            response = last_response.json()
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
