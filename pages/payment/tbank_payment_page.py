from playwright.sync_api import expect


class TBankPaymentPage:
    PAYMENT_STATUS_TIMEOUT = 30_000

    def __init__(self, page):
        self.page = page
        self.card_number = page.locator("[automation-id='tui-input-card-group__card']")
        self.expiry_date = page.locator("input[autocomplete='cc-exp']")
        self.cvc = page.locator("[automation-id='tui-input-card-group__cvc']")
        self.pay_button = page.locator("[automation-id='card-form__submit']")
        self.delete_card = page.get_by_text("Удалить карту")
        self.confirm_delete_card = page.locator(
            "[automation-id='delete-card-dialog__delete-button']"
        )

    def open(self, url):
        self.page.goto(url)
        self.card_number.wait_for()

    def assert_payment_form_opened(self):
        expect(self.card_number).to_be_visible()
        expect(self.expiry_date).to_be_visible()
        expect(self.cvc).to_have_count(1)
        expect(self.pay_button).to_be_visible()

    def remove_saved_card_if_present(self):
        if self.delete_card.is_visible():
            self.delete_card.click()
            self.confirm_delete_card.click()
            expect(self.confirm_delete_card).to_be_hidden()
            expect(self.card_number).to_be_visible()

    def fill_card(self, card):
        self.remove_saved_card_if_present()

        self.card_number.click()
        self.card_number.fill("")
        self.page.keyboard.type(card.number_card.replace(" ", ""), delay=80)
        self.page.keyboard.type(card.expiry_date.replace("/", ""), delay=80)
        self.page.keyboard.type(card.cvc, delay=80)

    def submit_payment(self):
        self.pay_button.click()

    def assert_payment_success(self):
        expect(self.page.locator("[automation-id='status-page']")).to_be_visible(
            timeout=self.PAYMENT_STATUS_TIMEOUT
        )
        expect(self.page.get_by_text("Оплачено")).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)

    def assert_payment_declined(self):
        expect(self.page.locator("[automation-id='status-page']")).to_be_visible(
            timeout=self.PAYMENT_STATUS_TIMEOUT
        )
        expect(self.page.get_by_text("Не получилось оплатить")).to_be_visible(
            timeout=self.PAYMENT_STATUS_TIMEOUT
        )
