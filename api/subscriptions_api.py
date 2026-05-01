from constants.constants import BASE_URL
from custom_requester.custom_requester import CustomRequester


class SubscriptionsAPI(CustomRequester):
    """
    Класс для работы с подпиской
    """

    SUBSCRIPTIONS = "subscriptions"
    SUBSCRIPTIONS_TRAIL = "subscriptions/trial"
    SUBSCRIPTIONS_USER = "subscriptions/users/"
    PAYMENT_INIT = "/payment/init"

    def __init__(self, session):
        super().__init__(session=session, base_url=BASE_URL)

    def get_subscriptions(self, expected_status=200):
        """
        Получить список доступных подписок
        :param expected_status: ожидаемый статус код
        """
        return self.send_request(
            method="GET", endpoint=self.SUBSCRIPTIONS, expected_status=expected_status
        )

    def get_subscriptions_users(self, user_id, expected_status=200):
        """
        Получить список подписок у конкретного пользователя
        :param user_id: ID пользователя
        :param expected_status: ожидаемый статус код
        """
        return self.send_request(
            method="GET",
            endpoint=f"{self.SUBSCRIPTIONS_USER}{user_id}",
            expected_status=expected_status,
        )

    def trial_subscription(self, expected_status=204):
        """
        Добавление пробной подписки
        :param expected_status: ожидаемый статус код
        """
        return self.send_request(
            method="GET", endpoint=self.SUBSCRIPTIONS_TRAIL, expected_status=expected_status
        )

    def subscriptions_payment_pending(self, subsId, email=None, expected_status=200):
        """
        Создание подписки с ссылкой на оплату
        :param subsId: ID подписки
        :param email: Email пользователя(необязательно, для предоставления платежных данных)
        :param expected_status:ожидаемый статус код
        """
        query_params = {}
        if email:
            query_params["email"] = email

        return self.send_request(
            method="GET",
            params=query_params,
            endpoint=f"{self.SUBSCRIPTIONS}/{subsId}{self.PAYMENT_INIT}",
            expected_status=expected_status,
        )

    def delete_subscriptions(self, request_body, expected_status=200):
        """
        Удаление подписки у пользователя
        :param request_body: тело запроса
        :param expected_status: ожидаемый статус код
        """
        return self.send_request(
            method="DELETE",
            data=request_body,
            endpoint=self.SUBSCRIPTIONS_USER,
            expected_status=expected_status,
        )
