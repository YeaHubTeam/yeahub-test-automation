import re

from playwright.sync_api import Locator, expect

from pages.interview.onboarding_modal import OnboardingModal

# В ТК фигурирует /dashboard/interview; приложение может отдавать /interview — оба допустимы.
INTERVIEW_URL_RE = re.compile(r".*interview(?:/|$|\?)", re.I)
CONFIRM_EMAIL_CTA_RE = re.compile(
    r"Подтвердить[\s\u00a0\u2011\-]*e?-?mail|Confirm[\s\u00a0]*e?-?mail",
    re.I,
)
INTERVIEW_TRAINER_TITLE_RE = re.compile(r"Тренаж[её]р\s+собеседований|Interview\s+trainer", re.I)


class InterviewPage:
    def __init__(self, page):
        self.page = page
        self.onboarding = OnboardingModal(page)

    def expect_on_interview_route(self) -> None:
        expect(self.page).to_have_url(INTERVIEW_URL_RE)

    def expect_authorized_after_login(self, *, username: str, email: str | None = None) -> None:
        """Шаг 4 ТК 409: редирект на interview и признак активной сессии (имя или email в шапке)."""
        expect(self.page).to_have_url(INTERVIEW_URL_RE, timeout=20_000)
        expect(self.page).not_to_have_url(re.compile(r".*/auth/login", re.I), timeout=10_000)
        identity = self.page.get_by_text(username).first
        if identity.is_visible(timeout=8_000):
            return
        if email and self.page.get_by_text(email).first.is_visible(timeout=8_000):
            return
        expect(identity).to_be_visible(timeout=12_000)

    def open_interview(self) -> None:
        self.page.goto("/interview", wait_until="domcontentloaded", timeout=60_000)
        self.expect_on_interview_route()

    def _confirm_email_cta(self) -> Locator:
        """CTA в шапке interview (после онбординга; на stage текст/разметка могут отличаться)."""
        header = self.page.locator("header")
        header_cta = header.locator(
            'a[href*="email-verify"], a[data-testid="Button"], button[data-testid="Button"]'
        ).filter(has_text=CONFIRM_EMAIL_CTA_RE)
        page_cta = self.page.locator(
            'a[href*="email-verify"], a[data-testid="Button"], button[data-testid="Button"]'
        ).filter(has_text=CONFIRM_EMAIL_CTA_RE)
        return (
            header_cta.or_(page_cta)
            .or_(header.get_by_text(CONFIRM_EMAIL_CTA_RE))
            .or_(self.page.get_by_role("button", name=CONFIRM_EMAIL_CTA_RE))
            .or_(self.page.get_by_role("link", name=CONFIRM_EMAIL_CTA_RE))
            .or_(self.page.get_by_text(CONFIRM_EMAIL_CTA_RE))
            .first
        )

    def expect_interview_trainer_page(self) -> None:
        """Предусловие 3 ТК 422: раздел «Тренажёр собеседований»."""
        self.expect_on_interview_route()
        expect(self.page.get_by_text(INTERVIEW_TRAINER_TITLE_RE).first).to_be_visible(
            timeout=15_000
        )

    def complete_onboarding_if_blocking_interview(self) -> None:
        """Онбординг после signUp/login: ждём модалку (SPA иногда рисует с задержкой), проходим 1/5–5/5."""
        onboarding = self.onboarding
        if not onboarding.modal.is_visible(timeout=20_000):
            if not self.page.get_by_role("heading", name="Onboarding").is_visible(timeout=3_000):
                return
        onboarding.complete_onboarding_through_close()

    def ensure_onboarding_completed_before_settings(self) -> None:
        """Перед переходом в settings: онбординг на /interview или повторно после навигации."""
        self.complete_onboarding_if_blocking_interview()
        if self.onboarding.modal.is_visible(timeout=1_000):
            self.onboarding.complete_onboarding_through_close()
            self.onboarding.expect_onboarding_dismissed()

    def prepare_interview_after_login(self) -> None:
        """Тренажёр + онбординг 1/5–5/5 (без ожидания CTA в шапке — на stage его может не быть)."""
        self.expect_interview_trainer_page()
        self.complete_onboarding_if_blocking_interview()

    def click_confirm_email_cta_if_visible(self, *, timeout_ms: int = 8_000) -> bool:
        """Шаг 1 ТК 422: клик по CTA в шапке, если есть. Иначе False → открыть /settings#email-verify."""
        cta = self._confirm_email_cta()
        if cta.is_visible(timeout=timeout_ms):
            cta.click(timeout=15_000)
            return True
        return False

    def open_profile_via_nav_link(self) -> None:
        """Раздел «Профиль»: пункт меню (link/button) или прямой /profile, если в UI нет role=link."""
        name_pat = re.compile(r"профил|profile", re.I)
        link = self.page.get_by_role("link", name=name_pat).first
        btn = self.page.get_by_role("button", name=name_pat).first
        if link.is_visible(timeout=5_000):
            link.click()
        elif btn.is_visible(timeout=3_000):
            btn.click()
        else:
            self.page.goto("/profile", wait_until="domcontentloaded", timeout=60_000)
        expect(self.page).to_have_url(re.compile(r"profile", re.I), timeout=20_000)

    def open_interview_via_nav_link(self) -> None:
        """Вернуться в «Интервью»: пункт меню или /interview."""
        name_pat = re.compile(r"интервью|interview", re.I)
        link = self.page.get_by_role("link", name=name_pat).first
        btn = self.page.get_by_role("button", name=name_pat).first
        if link.is_visible(timeout=5_000):
            link.click()
        elif btn.is_visible(timeout=3_000):
            btn.click()
        else:
            self.open_interview()
        self.expect_on_interview_route()
