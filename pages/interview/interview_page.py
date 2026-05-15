import re

from playwright.sync_api import expect

from pages.interview.onboarding_modal import OnboardingModal

# В ТК фигурирует /dashboard/interview; приложение может отдавать /interview — оба допустимы.
INTERVIEW_URL_RE = re.compile(r".*interview(?:/|$|\?)", re.I)


class InterviewPage:
    def __init__(self, page):
        self.page = page
        self.onboarding = OnboardingModal(page)

    def expect_on_interview_route(self) -> None:
        expect(self.page).to_have_url(INTERVIEW_URL_RE)

    def expect_authorized_after_login(self, *, username: str) -> None:
        """Шаг 4 ТК 409: редирект на interview и признак активной сессии (имя в шапке)."""
        self.expect_on_interview_route()
        expect(self.page).not_to_have_url(re.compile(r".*/auth/login", re.I), timeout=5_000)
        expect(self.page.get_by_text(username).first).to_be_visible(timeout=15_000)

    def open_interview(self) -> None:
        self.page.goto("/interview", wait_until="domcontentloaded", timeout=60_000)
        self.expect_on_interview_route()

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
