import re

from playwright.sync_api import expect


class RegisterPage:
    def __init__(self, page):
        self.page = page
        self._submit_button = page.get_by_role("button", name="Зарегистрироваться")
        self._username_input = page.locator('input[name="username"]')
        self._email_input = page.locator('input[name="email"]')
        self._password_input = page.locator('input[type="password"][name="password"]')
        self._password_confirmation = page.locator(
            'input[type="password"][name="passwordConfirmation"]'
        )

    @property
    def submit_button(self):
        return self._submit_button

    @property
    def username(self):
        return self._username_input

    @property
    def email(self):
        return self._email_input

    @property
    def password(self):
        return self._password_input

    @property
    def password_confirmation(self):
        return self._password_confirmation

    def open(self):
        self.page.goto("/auth/register", wait_until="domcontentloaded", timeout=60_000)
        self.expect_register_form_initial_state()

    def expect_register_form_initial_state(self) -> None:
        """ТК регистрация, шаг 1: форма, чекбоксы, кнопка неактивна."""
        fields = [
            self.username,
            self.email,
            self.password,
            self.password_confirmation,
        ]
        for field in fields:
            expect(field).to_be_visible()

        for name in ("privacyConsent", "offerConsent", "adConsent"):
            expect(self._consent_checkbox(name)).to_be_visible()

        expect(self.submit_button).to_be_visible()
        expect(self.submit_button).to_be_disabled()

    def expect_submit_disabled(self) -> None:
        expect(self.submit_button).to_be_disabled()

    def expect_submit_enabled(self) -> None:
        expect(self.submit_button).to_be_enabled()

    def open_with_clean_session(self) -> None:
        """После logout/удаления аккаунта: cookies + web storage, иначе повторная регистрация часто остаётся на /auth/register."""
        self.page.context.clear_cookies()
        self.page.goto("/auth/register", wait_until="domcontentloaded", timeout=60_000)
        self.page.evaluate(
            "() => { try { localStorage.clear(); sessionStorage.clear(); } catch (_) {} }",
        )
        self.expect_register_form_initial_state()

    def fill_register_form(self, username, email, password):
        self.username.fill(username)
        self.email.fill(email)
        self.password.fill(password)
        self.password_confirmation.fill(password)

    def _consent_checkbox(self, name: str):
        """Согласия: клик по label попадает в <a>, поэтому везде работаем с input."""
        return self.page.locator(f'input[type="checkbox"][name="{name}"]').first

    def _check_consent_by_name(self, name: str) -> None:
        """Controlled React: `check()` иногда не видит смену состояния — `set_checked` надёжнее."""
        box = self._consent_checkbox(name)
        expect(box).to_be_visible()
        box.set_checked(True, force=True)

    def check_privacy_consent(self) -> None:
        self._check_consent_by_name("privacyConsent")
        expect(self._consent_checkbox("privacyConsent")).to_be_checked()
        self.expect_submit_disabled()

    def check_offer_consent(self) -> None:
        self._check_consent_by_name("offerConsent")
        expect(self._consent_checkbox("offerConsent")).to_be_checked()
        self.expect_submit_enabled()

    def check_checkboxes(self) -> None:
        self.check_privacy_consent()
        self.check_offer_consent()

    def check_marketing_consent(self) -> None:
        """Опционально: согласие на рекламу (шаг 8 ТК — кнопка остаётся активной)."""
        self._check_consent_by_name("adConsent")
        expect(self._consent_checkbox("adConsent")).to_be_checked()
        self.expect_submit_enabled()

    def submit_registration(self):
        self.submit_button.click()

    def wait_after_successful_register(self):
        expect(self.page).to_have_url(
            re.compile(r".*/interview$"),
            timeout=15_000,
        )

    def finish_registration_after_api_signup(self, access_token: str) -> None:
        """SignUp уже выполнен через API-пробу: подставить токен в web storage и перейти на /interview без второго submit."""
        self.page.evaluate(
            """(token) => {
                for (const k of ['access_token', 'accessToken', 'token', 'authToken']) {
                    try { localStorage.setItem(k, token); } catch (_) {}
                }
            }""",
            access_token,
        )
        self.page.goto("/interview", wait_until="domcontentloaded", timeout=60_000)

    def expect_email_reuse_cooldown_toast(self) -> None:
        """После удаления аккаунта повторная регистрация на тот же email: API `user.user.email.limited_period`, в UI часто ключ i18n."""
        expect(
            self.page.get_by_text(re.compile(r"email\.limited_period|limited_period", re.I)).first,
        ).to_be_visible(timeout=15_000)
