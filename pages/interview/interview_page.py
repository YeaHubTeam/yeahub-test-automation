from playwright.sync_api import expect

from pages.interview.onboarding_modal import OnboardingModal


class InterviewPage:
    def __init__(self, page):
        self.page = page
        self.onboarding = OnboardingModal(page)
