import allure
import pytest

from api.api_manager import ApiManager
from models.user_response_model import Profiles, UserResponse

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression]


@allure.epic("Тест - Профиль пользователя")
@pytest.mark.api
@pytest.mark.smoke
class TestProfileYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Nikolay_Martoplyas")
    @allure.title("Тестирование получения профиля аутентифицированного пользователя")
    def test_auth_user_profile(self, api_manager: ApiManager, logged_in_user):
        with allure.step("Оправляем PATCH запрос с данными нового пароля пользователя"):
            response = api_manager.auth_api.profile(logged_in_user).json()
            response_data = UserResponse(**response)

        with allure.step("Проверяем, что зареганный пользователь пришел в ответе с профиля"):
            if "user" in response_data:
                assert response_data["user"]["username"] == logged_in_user["username"]
            else:
                assert response_data.get("username") == logged_in_user["username"]
