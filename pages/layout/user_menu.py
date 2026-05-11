import re

from playwright.sync_api import expect


class UserMenu:
    """Шапка: меню пользователя и быстрый переход в настройки."""

    def __init__(self, page):
        self.page = page

    def _profile_menu_trigger(self):
        """Кнопка с аватаром, открывающая меню (dialog/popover)."""
        return self.page.locator('button[aria-haspopup="dialog"]').filter(
            has=self.page.get_by_test_id("AvatarWithoutPhoto_Wrapper")
        )

    def open_profile_menu(self) -> None:
        trigger = self._profile_menu_trigger()
        expect(trigger).to_be_visible()
        trigger.click()

    def open_settings_via_profile_menu(self) -> None:
        """Меню профиля → пункт «Настройки» → /settings."""
        self.open_profile_menu()
        menu = self.page.locator('[role="menu"]').first
        expect(menu).to_be_visible(timeout=10_000)
        menu.get_by_text("Настройки", exact=True).click()
        expect(self.page).to_have_url(re.compile(r".*/settings"))

    def open_settings_via_preferences_button(self) -> None:
        """Иконка в шапке с aria-label go to preferences (если ведёт на /settings)."""
        self.page.get_by_role("button", name=re.compile(r"go to preferences", re.I)).click()
        expect(self.page).to_have_url(re.compile(r".*/settings"))
