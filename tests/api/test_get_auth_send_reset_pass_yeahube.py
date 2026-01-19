from api.api_manager import ApiManager

class TestSendResetPassYeahube:
    
    def test_get_auth_send_reset_pass_positive(self, api_manager: ApiManager, send_reset_pass_user):
        response = api_manager.auth_api.send_reset_pass(send_reset_pass_user)

        assert response.status_code == 200