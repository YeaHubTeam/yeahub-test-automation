import re

from playwright.sync_api import expect

from pages.interview.onboarding_modal import OnboardingModal


class UserMenu:
    """Шапка: меню пользователя и быстрый переход в настройки."""

    def __init__(self, page):
        self.page = page

    def _profile_menu_trigger(self):
        """Кнопка с аватаром, открывающая меню (dialog/popover)."""
        by_stub = self.page.locator('button[aria-haspopup="dialog"]').filter(
            has=self.page.get_by_test_id("AvatarWithoutPhoto_Wrapper")
        )
        if by_stub.count() > 0:
            return by_stub
        # Без заглушки «без фото» — ищем dialog-триггер в шапке (не `.first` по всей странице: там онбординг).
        header = self.page.locator("header")
        if header.count():
            return header.locator('button[aria-haspopup="dialog"]').last
        nav = self.page.locator("nav")
        if nav.count():
            return nav.locator('button[aria-haspopup="dialog"]').last
        return self.page.locator('button[aria-haspopup="dialog"]').last

    def _dismiss_modal_overlay_blocking_header(self) -> None:
        """Снять `Modal_Overlay`, чтобы клик по аватару дошёл до цели.

        Не используем Escape и клик по оверлею: на онбординге (особенно 2/5) это даёт
        валидацию «Специализация не выбрана» и лавину тостов — только штатный проход
        `complete_onboarding_through_close`.

        На /interview оверлей и Modal иногда монтируются после редиректа (TestIT, CI) —
        не выходим сразу при `Modal_Overlay` count=0, а коротко поллим.
        """
        onboarding = OnboardingModal(self.page)
        interview = "interview" in self.page.url.lower()
        max_rounds = 24 if interview else 4
        saw_overlay_in_dom = False

        for i in range(max_rounds):
            overlay_root = self.page.get_by_test_id("Modal_Overlay")
            if overlay_root.count():
                saw_overlay_in_dom = True

            if onboarding.modal.is_visible(timeout=600):
                onboarding.complete_onboarding_through_close()
                return

            if overlay_root.count() and overlay_root.first.is_visible(timeout=600):
                if onboarding.modal.is_visible(timeout=12_000):
                    onboarding.complete_onboarding_through_close()
                    return
                msg = (
                    "Modal overlay is visible but onboarding modal (Modal + stepper) was not found; "
                    "update locators or timeouts."
                )
                raise RuntimeError(msg)

            if not interview:
                return
            if interview and not saw_overlay_in_dom and i >= 12:
                return
            self.page.wait_for_timeout(350)

        overlay_root = self.page.get_by_test_id("Modal_Overlay")
        if overlay_root.count() and overlay_root.first.is_visible(timeout=400):
            msg = (
                "Modal overlay still visible after waiting for onboarding; "
                "UI may be slower than poll budget — increase max_rounds or fix hydration."
            )
            raise RuntimeError(msg)

    def open_profile_menu(self) -> None:
        self._dismiss_modal_overlay_blocking_header()
        trigger = self._profile_menu_trigger()
        expect(trigger).to_be_visible(timeout=12_000)
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
