import pytest

from payloads.auth_payloads import AuthPayloads
from utils.data_generator import DataGenerator

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.regression, pytest.mark.pr_safe]


class TestPasswordPositive:
    @pytest.mark.api
    def test_changing_password(self, logged_in_user, api_manager):
        """Смена пароля"""
        payload = AuthPayloads.payload_password()
        response = api_manager.auth_api.password_change(logged_in_user["id"], payload)
        assert response.json().get("access_token") is not None, "Токен не найден"

    @pytest.mark.api
    @pytest.mark.smoke
    def test_changing_password_and_login(self, logged_in_user, api_manager):
        """Смена пароля и логин под новым паролем"""
        payload = AuthPayloads.payload_password()
        response = api_manager.auth_api.password_change(logged_in_user["id"], payload)
        assert response.json().get("access_token") is not None, "Токен не найден"

        api_manager.auth_api.logout()
        login_data = {"username": logged_in_user["email"], "password": payload["password"]}
        response = api_manager.auth_api.login_user(login_data)
        response_date = response.json()
        assert response_date["user"]["id"] == logged_in_user["id"], "Ошибка ID не совпадают"
