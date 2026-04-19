import allure
import pytest

from pages.payment.tbank_payment_page import TBankPaymentPage
from payloads.card_payload import CardPayload


@pytest.mark.ui
@allure.epic("UI: Покупка подписки")
class TestSubscriptionPaymentUI:
    @allure.title("Успешная покупка подписки валидной картой")
    def test_user_can_buy_subscription_with_valid_card(self, page, payment_link_subscriptions):
        payment_page = TBankPaymentPage(page)

        payment_page.open(payment_link_subscriptions)
        payment_page.assert_payment_form_opened()
        payment_page.fill_card(CardPayload.VISA)
        payment_page.submit_payment()
        payment_page.assert_payment_success()

    def test_user_cannot_buy_subscription_with_invalid_cvc(self, page, payment_link_subscriptions):
        payment_page = TBankPaymentPage(page)

        payment_page.open(payment_link_subscriptions)
        payment_page.assert_payment_form_opened()
        payment_page.fill_card(CardPayload.INVALID_CVC)
