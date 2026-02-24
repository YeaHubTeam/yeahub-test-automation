from api.api_manager import ApiManager
import allure
import pytest

@allure.epic('Тест - Refresh authentication token')
@pytest.mark.api
@pytest.mark.smoke
class TestRefreshYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Dilovar_Odinaev")
    @allure.title('Тестирование обновления токена доступа')
    def test_refresh_auth_token(self, api_manager: ApiManager, logged_in_user):
        with allure.step('Отправляем запрос на получения нового токена доступа'):
            response = api_manager.auth_api.refresh_auth_token(logged_in_user)
            response_data = response.json()

        with allure.step('Проверяем что получили новый токен'):
            assert "access_token" in response_data or "accessToken" in response_data
