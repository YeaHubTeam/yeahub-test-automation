from api.api_manager import ApiManager

class TestLogoutYeahub:
    
    def test_get_auth_logout_positive(self, api_manager: ApiManager, logout_user):
        response = api_manager.auth_api.logout(logout_user)
        

