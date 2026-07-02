import re

from playwright.sync_api import expect

_PAY_TBANK_URL = re.compile(r"pay\.tbank\.ru", re.I)
_RETURN_TO_SHOP_RE = re.compile(
    r"^В\s+магазин$|^Return\s+to\s+(the\s+)?store$|вернуться\s+в\s+магазин|^To\s+the\s+shop$",
    re.I,
)
_SUCCESS_STATUS_RE = re.compile(
    r"Оплачено|Подтвержден|Успешн|оплачен|Paid|Successful|Success",
    re.I,
)
_DECLINED_STATUS_RE = re.compile(
    r"Не получилось оплатить|не удалось оплатить|Отклонен|отклонен|Unable to pay|Declined|Rejected",
    re.I,
)
_DELETE_CARD_RE = re.compile(r"Удалить карту|Delete card", re.I)
_POST_RETURN_ORIGIN_RE = re.compile(r"yeahub\.ru|yeatwork\.ru", re.I)


class TBankPaymentPage:
    PAYMENT_STATUS_TIMEOUT = 30_000

    def __init__(self, page):
        self.page = page
        self.card_number = page.locator("[automation-id='tui-input-card-group__card']")
        self.expiry_date = page.locator("input[autocomplete='cc-exp']")
        self.cvc = page.locator("[automation-id='tui-input-card-group__cvc']")
        self.pay_button = page.locator("[automation-id='card-form__submit']")
        self.delete_card = page.get_by_text(_DELETE_CARD_RE)
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

    def _pan_input(self):
        pan = self.card_number.locator("input")
        return pan.first if pan.count() else self.card_number

    def _is_pan_prefilled(self) -> bool:
        pan = self._pan_input()
        classes = (self.card_number.get_attribute("class") or "") + (
            pan.get_attribute("class") or ""
        )
        if "filled" in classes.lower():
            return True
        digits = re.sub(r"\D", "", pan.input_value())
        return len(digits) >= 4

    def _pan_matches(self, pan_digits: str) -> bool:
        last4 = pan_digits[-4:]
        visible = self._pan_input().input_value()
        if last4 in re.sub(r"\D", "", visible):
            return True
        actual = re.sub(r"\D", "", visible)
        return actual == pan_digits or actual.endswith(last4)

    def _type_digits(self, digits: str) -> None:
        self.page.keyboard.type(digits, delay=80)

    def fill_card(self, card):
        self.remove_saved_card_if_present()

        pan_digits = card.number_card.replace(" ", "")
        expiry_digits = card.expiry_date.replace("/", "")

        if self._is_pan_prefilled():
            # CVC overlay (t-wrapper_active) blocks clicks on PAN/expiry — only focus + keyboard.
            if self._pan_matches(pan_digits):
                expiry = self.expiry_date
                expiry.focus()
                expiry.press("ControlOrMeta+A")
                self._type_digits(expiry_digits)
                self._type_digits(card.cvc)
            else:
                pan = self._pan_input()
                pan.focus()
                pan.press("ControlOrMeta+A")
                self._type_digits(pan_digits)
                self._type_digits(expiry_digits)
                self._type_digits(card.cvc)
        else:
            self.card_number.click()
            self._type_digits(pan_digits)
            self._type_digits(expiry_digits)
            self._type_digits(card.cvc)

    def submit_payment(self):
        self.pay_button.click()

    def assert_payment_success(self):
        status_page = self.page.locator("[automation-id='status-page']")
        expect(status_page).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)
        success = (
            status_page.locator("[automation-id='payment__status_success']")
            .or_(status_page.get_by_text(_SUCCESS_STATUS_RE))
            .or_(status_page.get_by_role("button", name=_RETURN_TO_SHOP_RE))
            .or_(status_page.get_by_role("link", name=_RETURN_TO_SHOP_RE))
        )
        expect(success.first).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)

    def assert_payment_declined(self):
        status_page = self.page.locator("[automation-id='status-page']")
        expect(status_page).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)
        declined = status_page.locator("[automation-id='payment__status_rejected']").or_(
            status_page.get_by_text(_DECLINED_STATUS_RE)
        )
        expect(declined.first).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)

    def click_return_to_shop(self) -> None:
        """Шаг 6 ТК 116: «В магазин» на экране «Оплачено» (T-Bank sandbox)."""
        status_page = self.page.locator("[automation-id='status-page']")
        expect(status_page).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)
        return_btn = (
            status_page.locator("[automation-id='island__button']")
            .or_(status_page.get_by_role("button", name=_RETURN_TO_SHOP_RE))
            .or_(status_page.get_by_role("link", name=_RETURN_TO_SHOP_RE))
            .or_(status_page.get_by_text(_RETURN_TO_SHOP_RE))
        )
        expect(return_btn.first).to_be_visible(timeout=self.PAYMENT_STATUS_TIMEOUT)
        return_btn.first.click()

    def expect_left_tbank_after_return(self) -> None:
        expect(self.page).not_to_have_url(_PAY_TBANK_URL, timeout=30_000)
        expect(self.page).to_have_url(_POST_RETURN_ORIGIN_RE, timeout=30_000)
