import pytest

from utils.data_generator import DataGenerator


class TestPasswordPositive:
    @pytest.mark.api
    def test_changing_password(self, test_login, api_manager):
        """Смена пароля"""
        payload = DataGenerator.payload()
        response = api_manager.auth_api.password_exchange(test_login["id"], payload)
        assert response.json().get("access_token") is not None, "Токен не найден"

    @pytest.mark.api
    @pytest.mark.smoke
    def test_changing_password_and_login(self, test_login, api_manager):
        """Смена пароля и логин под новым паролем"""
        payload = DataGenerator.payload()
        response = api_manager.auth_api.password_exchange(test_login["id"], payload)
        assert response.json().get("access_token") is not None, "Токен не найден"

        api_manager.auth_api.logout()
        login_data = {"username": test_login["email"], "password": payload["password"]}
        response = api_manager.auth_api.login_user(login_data)
        response_date = response.json()
        assert response_date["user"]["id"] == test_login["id"], "Ошибка ID не совпадают"
