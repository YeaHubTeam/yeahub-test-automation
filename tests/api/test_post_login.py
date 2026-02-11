from api.api_manager import ApiManager


class TestLoginYeahub:
    def test_post_login_user_positive(self, api_manager: ApiManager, test_login):
        login_data = {
            "username": test_login["email"],
            "password": test_login["password"],
        }

        response = api_manager.auth_api.login_user(login_data)
        response_data = response.json()

        token = response_data.get("accessToken") or response_data.get("access_token")
        assert token, "Токен доступа отсутствует в ответе"
        assert isinstance(token, str), "Токен должен быть строкой"
        assert len(token) > 0, "Токен не должен быть пустым"

        assert "user" in response_data, "Данные пользователя отсутствуют в ответе"
        if "email" in response_data["user"]:
            assert response_data["user"]["email"] == test_login["email"], (
                "Email не совпадает"
            )

        assert "id" in response_data["user"], "ID пользователя отсутствует"
        assert "userRoles" in response_data["user"], "Роли пользователя отсутствуют"
