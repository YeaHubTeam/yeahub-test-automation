from api.api_manager import ApiManager


class User:
    SUPER_ADMIN_USERNAME = "mock-user@mock"
    SUPER_ADMIN_PASSWORD = "pwd-1234#secure"

    def __init__(self, email: str, password: str, roles: list, api: ApiManager):
        self.email = email
        self.password = password
        self.roles = roles
        self.api = api

    @property
    def creds(self):
        return self.email, self.password
