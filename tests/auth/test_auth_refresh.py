from api.api_manager import ApiManager

class TestRefreshYeahub:
    
    def test_get_auth_refresh_positive(self, api_manager: ApiManager, refresh_user):
        response = api_manager.auth_api.refresh_profile(refresh_user)
        response_data = response.json()


        assert "access_token" in response_data or "accessToken" in response_data
