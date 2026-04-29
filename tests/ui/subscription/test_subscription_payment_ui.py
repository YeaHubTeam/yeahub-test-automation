import allure
import pytest

from pages.payment.tbank_payment_page import TBankPaymentPage
from payloads.card_payload import CardPayload

pytestmark = [pytest.mark.ui, pytest.mark.integration, pytest.mark.regression]


@pytest.mark.ui
@allure.epic("UI: Покупка подписки")
class TestSubscriptionPaymentUI:
    @allure.title("Успешная покупка подписки валидной картой")
    def test_user_can_buy_subscription_with_valid_card(self, page, payment_link_subscriptions):
        payment_page = TBankPaymentPage(page)

        payment_page.open(payment_link_subscriptions)
        payment_page.assert_payment_form_opened()
        payment_page.fill_card(CardPayload.SUCCESS_CARD)
        payment_page.submit_payment()
        payment_page.assert_payment_success()

    @allure.title("Отклонение оплаты подписки decline-картой")
    def test_user_cannot_buy_subscription_with_declined_card(
        self, page, payment_link_subscriptions
    ):
        payment_page = TBankPaymentPage(page)

        payment_page.open(payment_link_subscriptions)
        payment_page.assert_payment_form_opened()
        payment_page.fill_card(CardPayload.DECLINED_CARD)
        payment_page.submit_payment()
        payment_page.assert_payment_declined()
