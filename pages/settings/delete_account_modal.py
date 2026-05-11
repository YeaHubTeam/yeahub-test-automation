import re

from playwright.sync_api import expect


class DeleteAccountModal:
    """Модалка подтверждения удаления аккаунта (Настройки → Аккаунт)."""

    def __init__(self, page):
        self.page = page
        self._modal = page.locator('[data-testid="Modal"]').filter(has_text="Удаление аккаунта")

    @property
    def modal(self):
        return self._modal

    @property
    def nickname_input(self):
        return self.modal.get_by_test_id("Input_Field")

    @property
    def confirm_button(self):
        return self.modal.get_by_test_id("Modal_Primary_Button")

    @property
    def cancel_button(self):
        return self.modal.get_by_test_id("Modal_Outline_Button")

    @property
    def close_button(self):
        return self.modal.get_by_test_id("Modal_Close_Icon")

    def expect_visible(self):
        expect(self.modal).to_be_visible()
        expect(self.modal.get_by_test_id("Modal_Title")).to_have_text("Удаление аккаунта")

    def fill_confirmation_nickname(self, username: str) -> None:
        self.nickname_input.fill(username)
        expect(self.confirm_button).to_be_enabled()

    def confirm_delete(self) -> None:
        self.confirm_button.click()

    def cancel(self) -> None:
        self.cancel_button.click()

    def close(self) -> None:
        self.close_button.click()

    def expect_hidden(self):
        expect(self.modal).to_be_hidden()

    def expect_redirect_to_register(self):
        expect(self.page).to_have_url(re.compile(r".*/auth/register"))

    def expect_account_deleted_toast(self):
        """Подстройте текст под фактический toasts после удаления."""
        expect(self.page.get_by_text(re.compile(r"удал|успеш", re.I)).first).to_be_visible(
            timeout=10_000
        )
