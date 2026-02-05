from api.api_manager import ApiManager


class TestSignUpYeahub:
    def test_post_signup_user_positive(self, api_manager: ApiManager, new_user_data):
        response = api_manager.auth_api.register_user(new_user_data)
        response_data = response.json()

        assert "access_token" in response_data, "Access token missing"
        assert "user" in response_data, "User data missing"
        assert response_data["user"]["username"] == new_user_data["username"]
        assert response_data["user"]["email"] == new_user_data["email"]
