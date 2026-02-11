from api.api_manager import ApiManager


class TestResetPasswordYeahub:
    def test_patch_reset_password_positive(
        self, api_manager: ApiManager, reset_password_user
    ):
        response = api_manager.auth_api.reset_password(reset_password_user)

        assert response.status_code == 200
