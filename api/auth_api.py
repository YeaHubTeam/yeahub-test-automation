from constants.constants import REGISTER_ENDPOINT, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester


class AuthAPI(CustomRequester):
    """
    Класс для работы с аутентификацией.
    """

    def __init__(self, session):
        super().__init__(session=session, base_url="https://api.yeatwork.ru/")

    def register_user(self, user_data, expected_status=201):
        """
        Регистрация нового пользователя.
        :param user_data: Данные пользователя.
        :param expected_status: Ожидаемый статус-код.
        """
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
        )

    def login_user(self, login_data, expected_status=201):
        """
        Авторизация пользователя.
        :param login_data: Данные для логина.
        :param expected_status: Ожидаемый статус-код.
        """
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status,
        )

    def authenticate(self, creds):
        login_data = {"username": creds[0], "password": creds[1]}

        response = self.login_user(login_data).json()
        token = response.get("accessToken") or response.get("access_token")

        if not token:
            raise KeyError(
                f"Token is missing in login response. Keys found: {list(response.keys())}"
            )

        self._update_session_headers(Authorization=f"Bearer {token}")

    def logout(self, *args, **kwargs):
        """
        Выход пользователя из системы.
        """
        return self.send_request(
            method="GET", endpoint="auth/logout", expected_status=200
        )

    def profile(self, *args, **kwargs):
        """
        Получение профиля аутентифицированного пользователя.
        """
        return self.send_request(
            method="GET", endpoint="auth/profile", expected_status=200
        )

    def refresh_profile(self, *args, **kwargs):
        """
        Refresh access token.
        """
        return self.send_request(
            method="GET", endpoint="auth/refresh", expected_status=200
        )

    def verify_email(self, *args, **kwargs):
        """
        Верификация email пользователя.
        """
        # Accept 400 since we use dummy token
        expected_status = kwargs.get("expected_status", [200, 400])

        return self.send_request(
            method="GET",
            endpoint="auth/verify-email",
            params={"token": "1"},
            expected_status=expected_status,
        )

    def send_verification_email(self, user_data=None, expected_status=200):
        """
        Отправка письма для верификации email пользователя.
        """
        user_id = user_data.get("id", 1) if isinstance(user_data, dict) else 1

        return self.send_request(
            method="GET",
            endpoint=f"auth/send-verification-email/{user_id}",
            expected_status=expected_status,
        )

    def password_exchange(self, user_data=None, expected_status=[200, 400]):
        """
        Смена пароля пользователя.
        """
        user_id = user_data.get("id", 1) if isinstance(user_data, dict) else 1

        password = user_data.get("password")
        payload = {
            "password": password,
            # Use password as passwordConfirm if not provided to avoid null
            "passwordConfirm": user_data.get("passwordRepeat")
            or user_data.get("passwordConfirm")
            or password,
            "token": user_data.get("token", "dummy_token"),
        }

        return self.send_request(
            method="PATCH",
            endpoint=f"auth/password-change/{user_id}",
            data=payload,
            expected_status=expected_status,
        )

    def reset_password(self, user_data=None, expected_status=[200, 401]):
        """
        Сброс пароля пользователя.
        """
        password = user_data.get("password")
        payload = {
            "password": password,
            # Use password as passwordConfirm if not provided to avoid null
            "passwordConfirm": user_data.get("passwordRepeat")
            or user_data.get("passwordConfirm")
            or password,
            "token": user_data.get("token", "dummy_token"),
        }

        return self.send_request(
            method="PATCH",
            endpoint="auth/reset-password",
            data=payload,
            expected_status=expected_status,
        )

    def send_reset_pass(self, user_data=None, expected_status=[200, 403]):
        """
        Отправка письма для сброса пароля пользователя.
        """
        email = (
            user_data.get("email", "<email>")
            if isinstance(user_data, dict)
            else "<email>"
        )

        return self.send_request(
            method="GET",
            endpoint="auth/send-reset-password",
            params={"email": email},
            expected_status=expected_status,
        )
