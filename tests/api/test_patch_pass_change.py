from api.api_manager import ApiManager


class TestPassChangeYeahub:
    def test_patch_pass_change_positive(self, api_manager: ApiManager, pass_exchange_user):

        response = api_manager.auth_api.password_exchange(pass_exchange_user)

        assert response.status_code == 200
