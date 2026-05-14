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

    def _profile_menu_trigger_loose(self):
        """Запасной триггер: кнопка с popover/menu в шапке (иногда без AvatarWithoutPhoto_Wrapper)."""
        return self.page.locator(
            'button[aria-haspopup="dialog"], button[aria-haspopup="menu"]'
        ).first

    def open_profile_menu(self) -> None:
        trigger = self._profile_menu_trigger()
        if trigger.is_visible(timeout=3_000):
            trigger.click()
        else:
            loose = self._profile_menu_trigger_loose()
            expect(loose).to_be_visible(timeout=10_000)
            loose.click()

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

    def logout_via_profile_menu(self) -> None:
        """Меню профиля → выход (popover не всегда с role=menu — ищем пункт глобально)."""
        self.open_profile_menu()
        logout_item = self.page.get_by_role(
            "menuitem",
            name=re.compile(r"Выйти|Выйти из|Log\s*out|Sign\s*out", re.I),
        ).first
        if logout_item.is_visible(timeout=8_000):
            logout_item.click()
            return
        fallback = self.page.get_by_text(
            re.compile(r"^\s*Выйти\s*$|Log\s*out|Sign\s*out", re.I),
        ).first
        expect(fallback).to_be_visible(timeout=12_000)
        fallback.click()
