import re

from playwright.sync_api import Page, expect

_PAY_TBANK_URL = re.compile(r"pay\.tbank\.ru", re.I)
_SUBSCRIBE_BTN = re.compile(r"^Подписаться$|^Subscribe$", re.I)
_MODAL_TITLE = re.compile(r"^Подписка$|^Subscription$", re.I)


class SubscriptionCheckoutModal:
    """Модальное окно оформления подписки после выбора тарифа."""

    def __init__(self, page: Page):
        self.page = page

    def _dialog(self):
        """На stage модалка — `[data-testid="Modal"]`, без `role=dialog`."""
        by_title = self.page.locator('[data-testid="Modal"]').filter(
            has=self.page.get_by_text(_MODAL_TITLE)
        )
        by_subscribe = self.page.locator('[data-testid="Modal"]').filter(
            has=self.page.get_by_role("button", name=_SUBSCRIBE_BTN)
        )
        return by_title.or_(by_subscribe).or_(self.page.get_by_role("dialog"))

    def expect_opened_with_email(self, email: str) -> None:
        dialog = self._dialog().first
        expect(dialog).to_be_visible(timeout=15_000)
        expect(dialog.get_by_text(_MODAL_TITLE).first).to_be_visible(timeout=10_000)
        email_field = dialog.locator(
            'input[type="email"], input[name*="email" i], input[readonly]'
        ).first
        if email_field.is_visible(timeout=3_000):
            expect(email_field).to_have_value(email, timeout=10_000)
        else:
            expect(dialog.get_by_text(re.compile(re.escape(email), re.I)).first).to_be_visible(
                timeout=10_000
            )

    def _consent_checkboxes(self):
        return self._dialog().first.locator('input[type="checkbox"]')

    def check_required_consents(self) -> None:
        """UI: 2 чекбокса (оферта+подписка объединены + сохранение учётных данных)."""
        boxes = self._consent_checkboxes()
        expect(boxes.first).to_be_visible(timeout=10_000)
        expect(boxes.nth(1)).to_be_visible(timeout=10_000)
        count = boxes.count()
        for i in range(count):
            box = boxes.nth(i)
            if not box.is_checked():
                box.set_checked(True, force=True)
            expect(box).to_be_checked()

    def _subscribe_button(self):
        return (
            self._dialog()
            .first.get_by_role("button", name=_SUBSCRIBE_BTN)
            .or_(self._dialog().first.get_by_test_id("Modal_Primary_Button"))
        )

    def expect_subscribe_enabled(self) -> None:
        expect(self._subscribe_button().first).to_be_enabled(timeout=10_000)

    def click_subscribe_and_expect_tbank(self) -> None:
        btn = self._subscribe_button().first
        expect(btn).to_be_enabled(timeout=10_000)
        btn.click()
        expect(self.page).to_have_url(_PAY_TBANK_URL, timeout=60_000)
