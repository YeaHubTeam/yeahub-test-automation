import re

from playwright.sync_api import expect

from pages.interview.onboarding_modal import OnboardingModal
from pages.settings.delete_account_modal import DeleteAccountModal

_DELETE_SECTION_TITLE = re.compile(r"Удаление\s+аккаунта|Delete\s+account", re.I)
_DELETE_TRIGGER_BTN = re.compile(r"^Удалить\s+аккаунт$|^Delete\s+account$", re.I)


class SettingsPage:
    def __init__(self, page):
        self.page = page
        self.delete_account_modal = DeleteAccountModal(page)

    def open(self) -> None:
        self.page.goto("/settings", wait_until="domcontentloaded", timeout=60_000)

    def open_account_direct(self) -> None:
        """Deep link на вкладку «Аккаунт»."""
        self.page.goto("/settings#account", wait_until="domcontentloaded", timeout=60_000)
        expect(self.page).to_have_url(re.compile(r".*/settings#account"))

    def open_account_tab(self) -> None:
        self.page.get_by_test_id("Tabs_Item_account").click()
        expect(self.page).to_have_url(re.compile(r".*/settings#account"))

    def _clear_onboarding_if_blocking(self) -> None:
        onboarding = OnboardingModal(self.page)
        if not onboarding.modal.is_visible(timeout=1_500):
            return
        if onboarding.try_dismiss_with_escape(presses=5):
            return
        try:
            onboarding.complete_onboarding_through_close()
        except AssertionError:
            pass

    def _delete_account_trigger(self):
        """Кнопка на странице настроек (не в модалке)."""
        return self.page.get_by_role("button", name=_DELETE_TRIGGER_BTN).first

    def _is_account_section_ready(self, timeout_ms: int = 3_000) -> bool:
        if OnboardingModal(self.page).modal.is_visible(timeout=500):
            return False
        try:
            expect(self.page.get_by_text(_DELETE_SECTION_TITLE).first).to_be_visible(
                timeout=timeout_ms
            )
            expect(self._delete_account_trigger()).to_be_visible(timeout=timeout_ms)
            return True
        except AssertionError:
            return False

    def open_account_ready(self) -> None:
        """`/settings#account` + снятие онбординга, пока недоступен блок удаления."""
        for _ in range(12):
            self.open_account_direct()
            if self._is_account_section_ready():
                return
            self._clear_onboarding_if_blocking()
            self.page.wait_for_timeout(400)
        self.expect_delete_account_section_visible()

    def expect_delete_account_section_visible(self) -> None:
        """Предусловие 2 ТК 117: вкладка «Аккаунт», блок «Удаление аккаунта»."""
        expect(self.page.get_by_text(_DELETE_SECTION_TITLE).first).to_be_visible(timeout=15_000)
        expect(self._delete_account_trigger()).to_be_visible(timeout=10_000)

    def open_delete_account_modal(self) -> None:
        self._clear_onboarding_if_blocking()
        expect(self._delete_account_trigger()).to_be_visible()
        self._delete_account_trigger().click()
        self.delete_account_modal.expect_visible()

    def delete_current_account(self, username: str) -> None:
        """Полный UI-поток удаления аккаунта до редиректа на регистрацию."""
        self.open_delete_account_modal()
        self.delete_account_modal.fill_confirmation_nickname(username)
        self.delete_account_modal.expect_confirm_delete_enabled()
        self.delete_account_modal.confirm_delete()
        self.delete_account_modal.expect_account_deleted_toast()
        self.delete_account_modal.expect_redirect_to_register()

    def delete_account_as_logged_in_user(self, username: str) -> None:
        """Открывает /settings, вкладку «Аккаунт», удаляет аккаунт (удобно для teardown)."""
        self.open()
        self.open_account_tab()
        self.delete_current_account(username)
