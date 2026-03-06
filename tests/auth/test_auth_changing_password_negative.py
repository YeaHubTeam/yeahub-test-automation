import pytest

from utils.data_generator import DataGenerator
from payloads.auth_payloads import AuthPayloads
from faker import Faker

faker = Faker()


class TestPasswordNegative:
    @pytest.mark.api
    def test_differend_passwords(self, logged_in_user, api_manager):
        """пароль и подьверждение пароля разные"""
        payload = AuthPayloads.payload_password(passwordConfirm=DataGenerator.random_password())
        response = api_manager.auth_api.password_change(
            logged_in_user["id"], payload, expected_status=400
        )
        assert response.json().get("description") == "Password confirmation failed", (
            "Сообщения не совпадают"
        )

    @pytest.mark.api
    def test_password_confirmation_empty(self, logged_in_user, api_manager):
        """Поле подтверждение пароля отсавляем пустым"""
        payload = AuthPayloads.payload_password(passwordConfirm="")
        response = api_manager.auth_api.password_change(
            logged_in_user["id"], payload, expected_status=400
        )
        assert response.json().get("description") == "Password confirmation failed", (
            "Сообщения не совпадают"
        )

    # TODO убрать маркер xfail после исправления бага
    @pytest.mark.api
    @pytest.mark.xfail(reason="По документации пароль не может быть меньше 8 символов")
    def test_password_less_than_eight_characters(self, logged_in_user, api_manager):
        """Пароль менее 8 символов"""
        password = faker.password(length=5)
        payload = AuthPayloads.payload_password(password=password, passwordConfirm=password)
        response = api_manager.auth_api.password_change(
            logged_in_user["id"], payload, expected_status=400
        )
        assert response.json().get("description") == "Password confirmation failed", (
            "Сообщения не совпадают"
        )

    @pytest.mark.api
    def test_login_old_password_after_change(
        self, logged_in_user, api_manager
    ):
        """Смена пароля и логин под старым паролем"""
        payload = AuthPayloads.payload_password()
        response = api_manager.auth_api.password_change(logged_in_user["id"], payload)
        assert response.json().get("access_token") is not None, "Токен не найден"

        api_manager.auth_api.logout()
        login_data = {
            "username": logged_in_user["email"],
            "password": logged_in_user["password"],
        }
        response_login = api_manager.auth_api.login_user(
            login_data, expected_status=401
        )
        assert (
            response_login.json().get("description")
            == "user with this email has another password"
        ), "Сообщения не совпадают"
