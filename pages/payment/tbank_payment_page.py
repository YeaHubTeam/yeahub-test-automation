from playwright.sync_api import expect


class TBankPaymentPage:
    def __init__(self, page):
        self.page = page
        self.card_number = page.locator("[automation-id='tui-input-card-group__card']")
        self.expiry_date = page.locator("input[autocomplete='cc-exp']")
        self.cvc = page.locator("[automation-id='tui-input-card-group__cvc']")
        self.pay_button = page.locator("[automation-id='card-form__submit']")

    def open(self, url):
        self.page.goto(url)
        self.card_number.wait_for()

    def assert_payment_form_opened(self):
        expect(self.card_number).to_be_visible()
        expect(self.expiry_date).to_be_visible()
        expect(self.cvc).to_have_count(1)
        expect(self.pay_button).to_be_visible()

    def fill_card(self, card):
        self.card_number.fill(card.number_card)
        self.expiry_date.fill(card.expiry_date)
        self.cvc.fill(card.cvc)

    def submit_payment(self):
        self.pay_button.click()

    def assert_payment_success(self):
        expect(self.page.locator("[automation-id='status-page']")).to_be_visible()
        expect(self.page.get_by_text("Оплачено")).to_be_visible()
