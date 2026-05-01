import allure
import pytest

from api.api_manager import ApiManager
from models.refresh_token_response_model import RefreshTokenResponse

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression, pytest.mark.pr_safe]


@allure.epic("Тест - Refresh authentication token")
@pytest.mark.api
@pytest.mark.smoke
class TestRefreshYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar_Odinaev")
    @allure.title("Тестирование обновления токена доступа")
    def test_refresh_auth_token(self, api_manager: ApiManager, logged_in_user):
        with allure.step("Отправляем запрос на получения нового токена доступа"):
            response = api_manager.auth_api.refresh_auth_token().json()
            response_data = RefreshTokenResponse(**response)

        with allure.step("Проверяем что получили новый токен"):
            assert "access_token" in response_data or "accessToken" in response_data
