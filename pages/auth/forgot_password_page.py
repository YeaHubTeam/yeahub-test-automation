import re

from playwright.sync_api import Page, expect


class ForgotPasswordPage:
    """Страница `/auth/forgot-password`."""

    def __init__(self, page: Page):
        self.page = page

    def _email_field(self):
        return (
            self.page.get_by_label(re.compile(r"email|почт|электрон", re.I))
            .or_(self.page.get_by_placeholder(re.compile(r"email|mail|почт", re.I)))
            .or_(self.page.locator('input[name="email"], input[name="username"]'))
            .first
        )

    def _submit_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Отправить$|^Send$", re.I)).first

    def expect_forgot_password_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/auth/forgot-password", re.I), timeout=20_000)
        expect(self._email_field()).to_be_visible(timeout=15_000)
        expect(self._submit_button()).to_be_visible(timeout=10_000)

    def fill_email(self, email: str) -> None:
        self._email_field().fill(email)

    def expect_no_validation_errors(self) -> None:
        expect(self.page.locator('input[aria-invalid="true"]')).to_have_count(0)

    def expect_submit_enabled(self) -> None:
        expect(self._submit_button()).to_be_enabled(timeout=10_000)

    def click_submit(self) -> None:
        self._submit_button().click()

    def expect_email_sent_modal(self) -> None:
        """Проверка успеха UI-отправки; модалку закрывать не нужно — дальше идёт IMAP/API."""
        expect(self.page.get_by_test_id("Modal")).to_be_visible(timeout=15_000)
        expect(self.page.get_by_test_id("Modal_Title")).to_contain_text(
            re.compile(r"отправили\s+письмо|sent\s+an\s+email", re.I),
            timeout=5_000,
        )
