import re

from playwright.sync_api import Page, expect

from pages.interview.interview_page import INTERVIEW_URL_RE


class PasswordRecoveryPage:
    """Страница `/auth/password-recovery?token=...` — смена пароля по ссылке из письма."""

    def __init__(self, page: Page):
        self.page = page

    def _new_password_field(self):
        return (
            self.page.get_by_label(
                re.compile(r"новый\s+пароль|new\s+password|введите\s+новый", re.I)
            )
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

    def _save_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Сохранить$|^Save$", re.I)).first

    def open(self, recovery_url: str) -> None:
        self.page.goto(recovery_url, wait_until="domcontentloaded", timeout=60_000)
        expect(self.page).to_have_url(
            re.compile(r".*/auth/password-recovery", re.I), timeout=20_000
        )
        self.expect_form_visible()

    def expect_form_visible(self) -> None:
        expect(
            self.page.get_by_text(
                re.compile(r"Изменение\s+пароля|Change\s+password|Reset\s+password", re.I)
            ).first
        ).to_be_visible(timeout=15_000)
        expect(self._new_password_field()).to_be_visible(timeout=10_000)
        expect(self._confirm_password_field()).to_be_visible(timeout=10_000)
        expect(self._save_button()).to_be_visible(timeout=10_000)

    def expect_no_validation_errors(self) -> None:
        expect(self.page.locator('input[type="password"][aria-invalid="true"]')).to_have_count(0)

    def fill_new_password(self, password: str) -> None:
        self._new_password_field().fill(password)

    def fill_confirm_password(self, password: str) -> None:
        self._confirm_password_field().fill(password)

    def expect_save_enabled(self) -> None:
        expect(self._save_button()).to_be_enabled(timeout=10_000)

    def click_save(self) -> None:
        self._save_button().click(timeout=15_000)

    def expect_success_toast(self) -> None:
        expect(
            self.page.get_by_text(
                re.compile(
                    r"Успешно.*Пароль\s+успешно\s+изменен|password.*successfully\s+changed",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=20_000)

    def expect_redirect_to_interview(self) -> None:
        expect(self.page).to_have_url(INTERVIEW_URL_RE, timeout=30_000)
