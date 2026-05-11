import re

from playwright.sync_api import expect


class OnboardingModal:
    def __init__(self, page):
        self.page = page
        self._modal = page.locator('[data-testid="Modal"]').filter(has_text="Onboarding")

    @property
    def modal(self):
        return self._modal

    @property
    def continue_btn(self):
        return self.modal.get_by_role("button", name="Продолжить")

    @property
    def save_and_continue_btn(self):
        return self.modal.get_by_role("button", name="Сохранить и продолжить")

    @property
    def later_btn(self):
        return self.modal.get_by_role("button", name="Позже")

    @property
    def close_icon(self):
        """Крестик в шапке модалки (на ранних шагах часто не кликабелен)."""
        return self.modal.get_by_test_id("Modal_Close_Icon")

    @property
    def onboarding_modal_close_btn(self):
        return self.close_icon

    def expect_onboarding_visible(self):
        expect(self.modal).to_be_visible()
        expect(self.modal.get_by_test_id("stepper")).to_be_visible()
        expect(self.modal.get_by_role("heading", name="Onboarding")).to_be_visible()

    def click_continue(self):
        self.continue_btn.click()

    def expect_onboarding_second_step_visible(self):
        expect(self.modal.get_by_role("heading", name="Выбери свою специализацию")).to_be_visible()
        expect(self.modal.get_by_test_id("dropdown-select")).to_be_visible()

    def open_drop_down_and_choose_specialization(self):
        self.modal.get_by_test_id("dropdown-select").click()
        self.page.get_by_role("option", name=re.compile(r"qa\s*engineer", re.I)).click()

    def click_save_and_continue(self):
        self.save_and_continue_btn.click()

    def expect_onboarding_third_step_visible(self):
        expect(
            self.modal.get_by_role(
                "heading", name="Сейчас на платформе есть сервис для подготовки к собеседованиям:"
            )
        ).to_be_visible()
        expect(self.continue_btn).to_be_visible()

    def expect_onboarding_fourth_step_visible(self):
        expect(
            self.modal.get_by_role(
                "heading", name="Ваша подписка помогает нам развивать платформу!"
            )
        ).to_be_visible()
        expect(self.later_btn).to_be_visible()

    def click_later_btn(self):
        self.later_btn.click()

    def expect_onboarding_fifth_step_visible(self):
        expect(
            self.modal.get_by_text(re.compile(r"YeaHub\s+становится\s+лучше", re.I))
        ).to_be_visible()

    def close_onboarding_modal(self):
        self.close_icon.click()

    def complete_onboarding_through_close(self) -> None:
        """Шаги 2–5: специализация → … → финал; крестик на последнем шаге.

        После долгого API/IMAP UI может остаться на 2-м шаге или уже уйти на 3+,
        поэтому каждый шаг выполняется только если виден его маркер.
        """
        expect(self.modal).to_be_visible(timeout=10_000)

        if self.modal.get_by_test_id("dropdown-select").is_visible(timeout=5_000):
            self.open_drop_down_and_choose_specialization()
            self.click_save_and_continue()

        # Шаг 3: заголовок часто не в <h*> — ищем фрагменты копирайта внутри модалки.
        step3_marker = self.modal.get_by_text(
            re.compile(
                r"Сейчас на платформе|сервис для подготовки|подготовк.*собеседован",
                re.I,
            )
        ).first
        if step3_marker.is_visible(timeout=8_000):
            self.click_continue()

        if self.later_btn.is_visible(timeout=8_000):
            self.click_later_btn()

        # Финальный экран: «5/5» и текст про YeaHub — два <p>; or_() даёт strict mode (2 элемента).
        expect(self.modal.get_by_text(re.compile(r"благодаря\s+вам", re.I)).first).to_be_visible(
            timeout=25_000
        )
        self.close_onboarding_modal()
        expect(self.modal).to_be_hidden(timeout=15_000)
