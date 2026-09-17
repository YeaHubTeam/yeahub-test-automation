import re

from playwright.sync_api import expect


class ModalDismissal:
    """Единая логика закрытия модалки онбординга: крестик → CTA → Escape.

    Раньше эта цепочка (с небольшими вариациями) была продублирована в
    close_onboarding_modal, _close_onboarding_if_still_open,
    finish_onboarding_after_fifth_step и _ensure_onboarding_dismissed
    исходного OnboardingModal. Здесь одна реализация — остальное её переиспользует.
    """

    _NAMED_DISMISS_PATTERN = re.compile(
        r"Закрыть|Готово|Понятно|Начать|Ок\b|\bOK\b|Done|Close|Got it",
        re.I,
    )

    def __init__(self, locators, page):
        self._loc = locators
        self.page = page

    def is_dismissed(self, timeout_ms: int = 2_000) -> bool:
        modal_gone = not self._loc.modal.is_visible(timeout=timeout_ms)
        heading_gone = not self.page.get_by_role("heading", name="Onboarding").is_visible(
            timeout=timeout_ms
        )
        return modal_gone and heading_gone

    def expect_dismissed(self, timeout_ms: int = 30_000) -> None:
        expect(self.page.get_by_role("heading", name="Onboarding")).to_be_hidden(
            timeout=timeout_ms
        )
        expect(self._loc.modal).to_be_hidden(timeout=5_000)

    def _try_click(self, locator, *, visibility_timeout_ms: int = 2_000) -> bool:
        if not locator.is_visible(timeout=visibility_timeout_ms):
            return False
        try:
            locator.click(timeout=10_000)
            expect(self._loc.modal).to_be_hidden(timeout=5_000)
            return True
        except AssertionError:
            return False

    def try_close_icon(self) -> bool:
        return self._try_click(self._loc.close_icon)

    def try_named_dismiss_button(self) -> bool:
        button = self._loc.modal.get_by_role("button", name=self._NAMED_DISMISS_PATTERN)
        return self._try_click(button.first)

    def try_primary_button(self) -> bool:
        return self._try_click(self._loc.primary_btn)

    def try_escape(self, *, presses: int = 3) -> bool:
        for _ in range(presses):
            if not self._loc.modal.is_visible(timeout=400):
                return True
            self.page.keyboard.press("Escape")
            try:
                expect(self._loc.modal).to_be_hidden(timeout=2_500)
                return True
            except AssertionError:
                pass
        return not self._loc.modal.is_visible(timeout=400)

    def dismiss(self) -> None:
        """Полная цепочка: крестик → именованная кнопка → primary CTA → Escape."""
        if self.is_dismissed(timeout_ms=1_000):
            return
        for strategy in (
                self.try_close_icon,
                self.try_named_dismiss_button,
                self.try_primary_button,
        ):
            if strategy():
                return
        self.try_escape(presses=2)
