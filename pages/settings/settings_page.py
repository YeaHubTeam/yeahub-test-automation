import re

from playwright.sync_api import expect

from pages.settings.delete_account_modal import DeleteAccountModal


class SettingsPage:
    def __init__(self, page):
        self.page = page
        self.delete_account_modal = DeleteAccountModal(page)

    def open(self) -> None:
        self.page.goto("/settings", wait_until="domcontentloaded", timeout=60_000)

    def open_account_direct(self) -> None:
        """Постусловие ТК: сразу раздел аккаунта."""
        self.page.goto("/settings#account", wait_until="domcontentloaded", timeout=60_000)
        expect(self.page).to_have_url(re.compile(r".*/settings#account"))

    def open_account_tab(self) -> None:
        self.page.get_by_test_id("Tabs_Item_account").click()
        expect(self.page).to_have_url(re.compile(r".*/settings#account"))

    def _delete_account_trigger(self):
        """Кнопка на странице настроек (не в модалке)."""
        return self.page.get_by_role("button", name="Удалить аккаунт").first

    def open_delete_account_modal(self) -> None:
        expect(self._delete_account_trigger()).to_be_visible()
        self._delete_account_trigger().click()
        self.delete_account_modal.expect_visible()

    def delete_current_account(self, username: str) -> None:
        """Полный UI-поток удаления аккаунта до редиректа на регистрацию."""
        self.open_delete_account_modal()
        self.delete_account_modal.fill_confirmation_nickname(username)
        self.delete_account_modal.confirm_delete()
        self.delete_account_modal.expect_redirect_to_register()

    def delete_account_as_logged_in_user(self, username: str) -> None:
        """Открывает /settings, вкладку «Аккаунт», удаляет аккаунт (удобно для teardown)."""
        self.open()
        self.open_account_tab()
        self.delete_current_account(username)
