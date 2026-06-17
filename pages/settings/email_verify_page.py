import re
import time

from playwright.sync_api import Page, expect


class EmailVerifyPage:
    """Раздел `/settings#email-verify` — верификация email (ТК 422)."""

    EMAIL_VERIFY_URL_RE = re.compile(r".*/settings#email-verify", re.I)
    _SECTION_TITLE = re.compile(r"Подтвердите\s+ваш\s+e-?mail|Verify\s+your\s+e-?mail", re.I)
    _VERIFICATION_SECTION = re.compile(r"Верификац", re.I)
    _EMAIL_SENT_TOAST = re.compile(
        r"Письмо\s+успешно\s+отправлено\s+на\s+почту|email.*successfully\s+sent",
        re.I,
    )
    _EMAIL_RATE_LIMIT_TOAST = re.compile(
        r"email\.limited_period|limited_period|restricted\s+in\s+a\s+period",
        re.I,
    )
    _EMAIL_SEND_ERROR_TOAST = re.compile(
        r"ошибк[аи].*отправк|произошл[ао].*ошибк|error.*send(?:ing)?|failed\s+to\s+send",
        re.I,
    )
    _RATE_LIMIT_SECONDS_RE = re.compile(
        r"restricted\s+in\s+a\s+period\s+of\s+(?P<seconds>[\d.]+)\s+seconds",
        re.I,
    )
    _EMAIL_CONFIRMED = re.compile(
        r"Почта\s+успешно\s+подтверждена|email.*successfully\s+verified",
        re.I,
    )
    _EMAIL_FIELD_LABEL = re.compile(r"Введите\s+e-?mail|enter\s+e-?mail", re.I)

    def __init__(self, page: Page):
        self.page = page

    _CONFIRM_SEND_RE = re.compile(r"^\s*Подтвердить\s*$|^\s*Confirm\s*$", re.I)

    def _email_verify_region(self):
        """Блок «Подтвердите ваш e-mail» (не путать с другими `data-testid=Button` на settings)."""
        return self.page.locator("div").filter(has=self.page.get_by_text(self._SECTION_TITLE))

    def _confirm_button(self):
        """`<button data-testid=\"Button\">Подтвердить</button>` справа от поля email."""
        in_section = (
            self._email_verify_region()
            .locator('button[data-testid="Button"]')
            .filter(has_text=self._CONFIRM_SEND_RE)
        )
        return (
            in_section.or_(
                self.page.locator('button[data-testid="Button"]').filter(
                    has_text=self._CONFIRM_SEND_RE
                )
            )
            .or_(self.page.get_by_role("button", name=self._CONFIRM_SEND_RE))
            .first
        )

    def _email_input(self):
        by_wrapper = self._email_verify_region().get_by_test_id("Input_Wrapper").locator("input")
        return (
            by_wrapper.or_(self.page.get_by_label(self._EMAIL_FIELD_LABEL))
            .or_(self.page.get_by_placeholder(self._EMAIL_FIELD_LABEL))
            .or_(self.page.locator('input[type="email"]'))
            .first
        )

    def expect_on_email_verify_route(self) -> None:
        expect(self.page).to_have_url(self.EMAIL_VERIFY_URL_RE, timeout=20_000)

    def expect_verification_section_visible(self) -> None:
        expect(self.page.get_by_text(self._VERIFICATION_SECTION).first).to_be_visible(
            timeout=15_000
        )
        expect(self.page.get_by_text(self._SECTION_TITLE).first).to_be_visible(timeout=15_000)

    def expect_email_field_with_value(self, email: str) -> None:
        field = self._email_input()
        expect(field).to_be_visible(timeout=10_000)
        expect(field).to_have_value(email, timeout=5_000)

    def expect_email_sent_toast_visible(self) -> None:
        expect(self.page.get_by_text(self._EMAIL_SENT_TOAST).first).to_be_visible(timeout=20_000)

    def expect_email_sent_toast_hidden(self) -> None:
        expect(self.page.get_by_text(self._EMAIL_SENT_TOAST).first).not_to_be_visible(
            timeout=10_000
        )

    def ensure_verification_tab(self) -> None:
        """Вкладка «Верификация» на /settings (hash иногда не переключает таб после reload)."""
        for test_id in ("Tabs_Item_email-verify", "Tabs_Item_emailVerify", "Tabs_Item_verify"):
            tab = self.page.get_by_test_id(test_id)
            if tab.count() and tab.is_visible(timeout=1_500):
                tab.click()
                break
        else:
            tab_by_name = self.page.get_by_role("tab", name=self._VERIFICATION_SECTION)
            if tab_by_name.first.is_visible(timeout=2_000):
                tab_by_name.first.click()
        self.expect_on_email_verify_route()

    def expect_after_first_open(self, *, email: str) -> None:
        """Шаг 1: /settings#email-verify, поле email; тост после клика CTA или первого входа (если есть)."""
        self.expect_on_email_verify_route()
        self.ensure_verification_tab()
        self.expect_verification_section_visible()
        self.expect_email_field_with_value(email)
        toast = self.page.get_by_text(self._EMAIL_SENT_TOAST).first
        if not toast.is_visible(timeout=5_000):
            return
        expect(toast).to_be_visible(timeout=5_000)

    def open_step1_from_interview(self, interview_page) -> None:
        """Шаг 1: CTA в шапке interview или прямой переход на verify (fallback для API signUp)."""
        interview_page.prepare_interview_after_login()
        if not interview_page.click_confirm_email_cta_if_visible():
            self.open_email_verify_direct()
        else:
            self.expect_on_email_verify_route()
            self.ensure_verification_tab()

    def reload_page(self) -> None:
        self.page.reload(wait_until="domcontentloaded", timeout=60_000)
        self.ensure_verification_tab()

    def expect_form_after_reload(self, *, email: str) -> None:
        """Шаг 2: форма без тоста (тост может кратко мигать после reload — ждём скрытия)."""
        self.expect_verification_section_visible()
        expect(self.page.get_by_text(self._SECTION_TITLE).first).to_be_visible(timeout=15_000)
        self.expect_email_field_with_value(email)
        expect(self._confirm_button()).to_be_visible(timeout=15_000)
        toast = self.page.get_by_text(self._EMAIL_SENT_TOAST).first
        if toast.is_visible(timeout=2_000):
            expect(toast).not_to_be_visible(timeout=20_000)
        else:
            expect(toast).not_to_be_visible(timeout=5_000)

    def is_email_sent_toast_visible(self, *, timeout_ms: int = 3_000) -> bool:
        return self.page.get_by_text(self._EMAIL_SENT_TOAST).first.is_visible(timeout=timeout_ms)

    def _visible_send_error_toast_text(self) -> str | None:
        for pattern in (self._EMAIL_SEND_ERROR_TOAST, self._EMAIL_RATE_LIMIT_TOAST):
            err = self.page.get_by_text(pattern).first
            if err.is_visible(timeout=800):
                return err.inner_text(timeout=2_000)
        return None

    def _rate_limit_wait_seconds(
        self, error_text: str | None, *, response_status: int | None
    ) -> float:
        if response_status == 403:
            return 65.0
        if error_text:
            match = self._RATE_LIMIT_SECONDS_RE.search(error_text)
            if match:
                return float(match.group("seconds")) + 1.0
            if self._EMAIL_SEND_ERROR_TOAST.search(
                error_text
            ) or self._EMAIL_RATE_LIMIT_TOAST.search(error_text):
                return 65.0
        return 65.0

    def click_confirm_send_email(self, *, max_attempts: int = 4) -> bool:
        """Шаг 3: клик «Подтвердить». True — тост успеха; False — ошибка/rate limit (письмо могло уйти при signUp)."""
        btn = self._confirm_button()
        last_error: str | None = None
        last_status: int | None = None

        for attempt in range(max_attempts):
            expect(btn).to_be_enabled(timeout=15_000)
            btn.scroll_into_view_if_needed(timeout=5_000)
            response_status: int | None = None
            try:
                with self.page.expect_response(
                    lambda r: (
                        "send-verification-email" in r.url and r.request.method in ("GET", "POST")
                    ),
                    timeout=30_000,
                ) as resp_info:
                    btn.click(timeout=15_000)
                response_status = resp_info.value.status
                last_status = response_status
            except Exception:
                btn.click(timeout=15_000)

            if self.is_email_sent_toast_visible(timeout_ms=25_000):
                return True

            last_error = self._visible_send_error_toast_text()
            if (last_error or response_status == 403) and attempt < max_attempts - 1:
                time.sleep(
                    self._rate_limit_wait_seconds(last_error, response_status=response_status)
                )
                continue

        return False

    def expect_after_resend_click(self) -> None:
        """Шаг 3: успешный тост (если UI-отправка прошла без rate limit)."""
        self.expect_email_sent_toast_visible()

    def expect_email_verified_state(self) -> None:
        """Шаг 6: почта подтверждена."""
        self.expect_on_email_verify_route()
        expect(self.page.get_by_text(self._EMAIL_CONFIRMED).first).to_be_visible(timeout=20_000)

    def open_email_verify_direct(self) -> None:
        self.page.goto("/settings#email-verify", wait_until="domcontentloaded", timeout=60_000)
        self.ensure_verification_tab()
