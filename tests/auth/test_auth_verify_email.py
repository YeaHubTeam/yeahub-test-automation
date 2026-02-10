from api.api_manager import ApiManager

class TestVerifyEmailYeahub:
    
    def test_get_auth_verify_email_positive(self, api_manager: ApiManager, verify_email_user):
        response = api_manager.auth_api.verify_email(verify_email_user)
        

