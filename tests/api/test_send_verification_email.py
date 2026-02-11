from api.api_manager import ApiManager


class TestSendVerificationEmailYeahub:
    def test_get_send_verification_email_positive(
        self, api_manager: ApiManager, verification_user
    ):
        response = api_manager.auth_api.send_verification_email(verification_user)

        assert response.status_code == 200
