import re

from playwright.sync_api import Page, expect

from pages.interview.onboarding_modal import OnboardingModal


class ChangePasswordPage:
    """Раздел `/settings#change-password`."""

    def __init__(self, page: Page):
        self.page = page

    def _new_password_field(self):
        return (
            self.page.get_by_label(re.compile(r"новый\s+пароль|new\s+password", re.I))
            .or_(
                self.page.get_by_placeholder(
                    re.compile(r"новый\s+пароль|new\s+password|enter.*new", re.I)
                )
            )
            .or_(self.page.locator('input[type="password"]').first)
        ).first

    def _confirm_password_field(self):
        return (
            self.page.get_by_label(re.compile(r"повтор|confirm|repeat", re.I))
            .or_(self.page.get_by_placeholder(re.compile(r"повтор|confirm|repeat", re.I)))
            .or_(self.page.locator('input[type="password"]').nth(1))
        ).first

    def _change_password_section(self):
        return self.page.locator("#change-password").or_(
            self.page.locator('[id="change-password"]')
        )

    def _save_button(self):
        section = self._change_password_section()
        btn = section.get_by_role("button", name=re.compile(r"^Сохранить$|^Save$", re.I))
        if btn.count():
            return btn.first
        return self.page.get_by_role("button", name=re.compile(r"^Сохранить$|^Save$", re.I)).first

    def _clear_onboarding_blocking_settings(self) -> None:
        """Снять онбординг, если он перекрывает settings (часто застревает на 2/5 — специализация)."""
        onboarding = OnboardingModal(self.page)
        if not onboarding.modal.is_visible(timeout=1_500):
            return
        if onboarding.try_dismiss_with_escape(presses=5):
            return
        progress_1 = onboarding.modal.get_by_text(re.compile(r"1\s*/\s*5|1\s+of\s+5", re.I)).first
        if progress_1.is_visible(timeout=2_000) and onboarding.continue_btn.is_visible(
            timeout=2_000
        ):
            onboarding.click_continue()
        if onboarding.modal.get_by_test_id("dropdown-select").is_visible(timeout=3_000):
            try:
                onboarding.complete_tc_steps_2_through_7()
            except AssertionError:
                pass
            return
        try:
            onboarding.complete_onboarding_through_close()
        except AssertionError:
            pass

    def _dismiss_onboarding_if_visible(self) -> None:
        self._clear_onboarding_blocking_settings()

    def _wait_until_form_ready(self, *, max_attempts: int = 12) -> None:
        """Критерий готовности — форма смены пароля, а не «модалка скрыта»."""
        for _ in range(max_attempts):
            if self._is_form_ready(timeout_ms=3_000):
                return
            if OnboardingModal(self.page).modal.is_visible(timeout=800):
                self._clear_onboarding_blocking_settings()
            else:
                self.open_change_password()
            self.page.wait_for_timeout(400)
        self.expect_change_password_form_visible()

    def open_change_password(self) -> None:
        self.page.goto(
            "/settings#change-password",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        expect(self.page).to_have_url(
            re.compile(r".*/settings.*change-password", re.I), timeout=20_000
        )

    def _is_form_ready(self, timeout_ms: int = 8_000) -> bool:
        onboarding = OnboardingModal(self.page)
        if onboarding.modal.is_visible(timeout=500):
            return False
        try:
            expect(self._new_password_field()).to_be_visible(timeout=timeout_ms)
            expect(self._save_button()).to_be_visible(timeout=3_000)
            return True
        except AssertionError:
            return False

    def open_change_password_ready(self) -> None:
        """Deep link на settings; онбординг снимаем только пока форма недоступна."""
        self.open_change_password()
        self._wait_until_form_ready()

    def expect_change_password_form_visible(self) -> None:
        expect(self._new_password_field()).to_be_visible(timeout=15_000)
        expect(self._confirm_password_field()).to_be_visible(timeout=10_000)
        expect(self._save_button()).to_be_visible(timeout=10_000)

    def expect_no_validation_errors(self) -> None:
        expect(self.page.locator('input[type="password"][aria-invalid="true"]')).to_have_count(0)

    def fill_new_password(self, password: str) -> None:
        self._dismiss_onboarding_if_visible()
        self._new_password_field().fill(password)

    def fill_confirm_password(self, password: str) -> None:
        self._dismiss_onboarding_if_visible()
        self._confirm_password_field().fill(password)

    def expect_save_enabled(self) -> None:
        expect(self._save_button()).to_be_enabled(timeout=10_000)

    def expect_save_disabled(self) -> None:
        expect(self._save_button()).to_be_disabled(timeout=10_000)

    def click_save(self) -> None:
        self._dismiss_onboarding_if_visible()
        save_btn = self._save_button()
        expect(save_btn).to_be_enabled(timeout=10_000)
        save_btn.click(timeout=15_000)

    def expect_success_notification(self) -> None:
        expect(
            self.page.get_by_text(
                re.compile(
                    r"Успешно.*Пароль\s+успешно\s+изменен|password.*successfully\s+changed",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=15_000)

    def expect_form_reset_after_success(self) -> None:
        expect(self._new_password_field()).to_have_value("", timeout=10_000)
        expect(self._confirm_password_field()).to_have_value("")
        self.expect_save_disabled()
