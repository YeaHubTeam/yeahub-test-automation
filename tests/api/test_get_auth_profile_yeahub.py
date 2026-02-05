from api.api_manager import ApiManager


class TestProfileYeahub:
    def test_get_auth_profile_positive(self, api_manager: ApiManager, profile_user):
        response = api_manager.auth_api.profile(profile_user)
        response_data = response.json()

        assert response.status_code == 200
        if "user" in response_data:
            assert response_data["user"]["username"] == profile_user["username"]
        else:
            assert response_data.get("username") == profile_user["username"]
