from api.auth_api import AuthAPI
from api.user_api import UserAPI
from api.subscriptions_api import SubscriptionsAPI


class ApiManager:
    def __init__(self, session):
        self.session = session
        self.auth_api = AuthAPI(session)
        self.user_api = UserAPI(session)
        self.subscriptions_api = SubscriptionsAPI(session)

    def close_session(self):
        self.session.close()
