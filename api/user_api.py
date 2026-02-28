from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL


class UserAPI(CustomRequester):
    """
    Класс для получения информации о пользователе, удаления и тд.
    """

    USER_ENDPOINT = "users/"

    def __init__(self, session):
        super().__init__(session=session, base_url=BASE_URL)

    def delete_user(self, user_id, expected_status=200):
        """
        Метод для удвления пользователя
        :param user_id: ID пользователя
        """
        return self.send_request(
            method="DELETE",
            endpoint=f"{self.USER_ENDPOINT}{user_id}",
            expected_status=expected_status,
        )

    def get_user(self, user_id, expected_status=200):
        """
        Метод для поиска пользователя по ID
        :param user_id: ID пользователя
        :param expected_status: ожидаемый статус код
        """

        return self.send_request(
            method="GET",
            endpoint=f"{self.USER_ENDPOINT}{user_id}",
            expected_status=expected_status,
        )
