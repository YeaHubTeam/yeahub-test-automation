import re

from playwright.sync_api import expect


class LoginPage:
    """Страница `/auth/login` (username в API = email)."""

    def __init__(self, page):
        self.page = page

    def open(self) -> None:
        """`commit` — не ждём полный `domcontentloaded` (на SPA иногда висит из‑за ресурсов)."""
        self.ensure_on_login_page()

    def clear_browser_session(self) -> None:
        """Cookies + web storage — иначе SPA после recovery остаётся авторизованной на /."""
        self.page.context.clear_cookies()
        self.page.evaluate(
            "() => { try { localStorage.clear(); sessionStorage.clear(); } catch (_) {} }",
        )

    def ensure_on_login_page(self, *, timeout_ms: int = 90_000) -> None:
        """Открыть форму login; при активной SPA-сессии — сбросить storage и повторить переход."""
        self.page.goto("/auth/login", wait_until="commit", timeout=60_000)
        if not re.search(r"/auth/login", self.page.url):
            self.clear_browser_session()
            self.page.goto("/auth/login", wait_until="commit", timeout=60_000)
        expect(self.page).to_have_url(re.compile(r".*/auth/login"), timeout=timeout_ms)
        expect(self.page.locator('input[name="username"]')).to_be_visible(timeout=timeout_ms)

    def _expect_password_visibility_toggle_visible(self) -> None:
        """Иконка показа пароля: span с ``data-testid="Input_Suffix"`` и ``svg`` (app.yeatwork.ru)."""
        pwd = self.page.locator('input[type="password"]').first
        expect(pwd).to_be_visible(timeout=5_000)
        toggle = (
            pwd.locator("..")
            .get_by_test_id("Input_Suffix")
            .or_(pwd.locator("xpath=following::span[@data-testid='Input_Suffix'][1]"))
            .or_(pwd.locator("xpath=preceding::span[@data-testid='Input_Suffix'][1]"))
            .first
        )
        expect(toggle).to_be_visible(timeout=10_000)
        expect(toggle.locator("svg")).to_be_visible(timeout=5_000)

    def expect_login_form_elements_visible(self) -> None:
        """Ручной ТК 409, шаг 1: состав формы (без кнопки Telegram — вне объёма проверки)."""
        expect(
            self.page.get_by_role("heading", name=re.compile(r"Вход\s+в\s+личный\s+кабинет", re.I))
        ).to_be_visible(timeout=15_000)
        # Поле email: на стенде часто нет <label for> — матчим label, placeholder или name=username.
        email_field = (
            self.page.get_by_label(re.compile(r"Электронн", re.I))
            .or_(self.page.get_by_placeholder(re.compile(r"email|mail|почт|электрон", re.I)))
            .or_(self.page.locator('input[name="username"]'))
            .first
        )
        expect(email_field).to_be_visible(timeout=10_000)
        pwd_field = (
            self.page.get_by_label(re.compile(r"Пароль", re.I))
            .or_(self.page.locator('input[type="password"]'))
            .first
        )
        expect(pwd_field).to_be_visible(timeout=10_000)

        self._expect_password_visibility_toggle_visible()

        # «Забыли пароль?» — `<a data-testid="Button">` (на форме несколько `Button` — фильтр по тексту).
        forgot_pw = (
            self.page.locator('a[data-testid="Button"]')
            .filter(has_text=re.compile(r"забыли[\s\u00a0]*парол", re.I))
            .first.or_(
                self.page.get_by_role(
                    "link", name=re.compile(r"забыли.*парол|forgot.*password", re.I)
                )
            )
            .or_(
                self.page.locator('a[href*="forgot"], a[href*="password"], a[href*="reset"]').first
            )
        )
        expect(forgot_pw.first).to_be_visible(timeout=10_000)
        expect(
            self.page.get_by_role("button", name=re.compile(r"^Вход$|^Войти$", re.I))
        ).to_be_visible(timeout=10_000)
        # «Зарегистрироваться» — часто тот же паттерн, что «Забыли пароль?»: `<a data-testid="Button">`.
        signup = (
            self.page.locator('a[data-testid="Button"]')
            .filter(has_text=re.compile(r"зарегистрир", re.I))
            .first.or_(
                self.page.get_by_role(
                    "link", name=re.compile(r"зарегистрир|sign\s*up|register", re.I)
                )
            )
            .or_(self.page.locator('a[href*="/auth/register"], a[href*="register"]').first)
        )
        expect(signup.first).to_be_visible(timeout=10_000)

    def expect_no_login_validation_errors(self) -> None:
        """Нет явной клиентской ошибки у полей (HTML5 / подписи под полем)."""
        expect(self.page.locator('input[name="username"][aria-invalid="true"]')).to_have_count(0)
        expect(self.page.locator('input[type="password"][aria-invalid="true"]')).to_have_count(0)
        expect(
            self.page.get_by_text(
                re.compile(r"обязательное\s+поле|некорректн.*почт|invalid\s+email", re.I)
            ).first
        ).not_to_be_visible()

    def fill_credentials(self, email: str, password: str) -> None:
        self.page.locator('input[name="username"]').fill(email)
        self.page.locator('input[type="password"]').fill(password)

    def submit(self) -> None:
        self.page.get_by_role("button", name=re.compile(r"Войти|Вход|Sign\s*in", re.I)).click()

    def submit_expecting_unauthorized(self) -> None:
        """ТК 117 шаг 7: login удалённого пользователя → HTTP 401/403, остаёмся на /auth/login."""
        with self.page.expect_response(
            lambda r: "/auth/login" in r.url and r.request.method == "POST",
            timeout=20_000,
        ) as resp_info:
            self.submit()
        status = resp_info.value.status
        assert status in (401, 403), f"Expected login failure HTTP 401/403, got {status}"
        self.expect_still_on_login_after_failed_attempt()

    def expect_still_on_login_after_failed_attempt(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/auth/login", re.I), timeout=15_000)
        expect(self.page).not_to_have_url(re.compile(r".*/interview", re.I), timeout=5_000)
        self.expect_login_form_elements_visible()

    def expect_login_failed(self) -> None:
        """Ошибка входа: остаёмся на login; при наличии — toast/текст ошибки."""
        self.expect_still_on_login_after_failed_attempt()
        error = self.page.get_by_text(
            re.compile(
                r"неверн.*парол|неверный\s+логин|invalid\s+credential|"
                r"wrong\s+password|authentication\s+failed|"
                r"не\s+удалось\s+войти|ошибк.*авториз|"
                r"public_unauthorized|auth\.auth\.|unauthorized",
                re.I,
            )
        ).first
        if error.is_visible(timeout=2_000):
            return
        toast = self.page.locator('[data-testid*="Toast"], [role="alert"]').first
        expect(toast).to_be_visible(timeout=2_000)

    def click_forgot_password(self) -> None:
        """Шаг 2 ТК 115: «Забыли пароль?» → /auth/forgot-password."""
        forgot_pw = (
            self.page.locator('a[data-testid="Button"]')
            .filter(has_text=re.compile(r"забыли[\s\u00a0]*парол", re.I))
            .first.or_(
                self.page.get_by_role(
                    "link", name=re.compile(r"забыли.*парол|forgot.*password", re.I)
                )
            )
            .or_(
                self.page.locator('a[href*="forgot"], a[href*="password"], a[href*="reset"]').first
            )
        )
        forgot_pw.first.click()
        expect(self.page).to_have_url(re.compile(r".*/auth/forgot-password", re.I), timeout=20_000)

    def open_app_expect_login(self) -> None:
        """Предусловие: неавторизованный пользователь на / → редирект на login."""
        self.page.goto("/", wait_until="domcontentloaded", timeout=60_000)
        expect(self.page).to_have_url(re.compile(r".*/auth/login", re.I), timeout=30_000)
