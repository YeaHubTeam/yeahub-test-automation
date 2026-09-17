import re

from playwright.sync_api import expect

from pages.interview.onboarding.dismissal import ModalDismissal
from pages.interview.onboarding.locators import OnboardingLocators
from pages.interview.onboarding.specialization_step import SpecializationStep
from pages.interview.onboarding.step_visibility import StepVisibility


class OnboardingModal:
    """Page Object модалки онбординга.

    Публичный API идентичен исходной версии — весь код тестов и фикстур,
    вызывающий эти методы, продолжает работать без изменений. Внутри —
    делегирование в компоненты с одной ответственностью каждый:
    OnboardingLocators / StepVisibility / SpecializationStep / ModalDismissal.
    """

    def __init__(self, page):
        self.page = page
        self._locators = OnboardingLocators(page)
        self._steps = StepVisibility(self._locators)
        self._specialization = SpecializationStep(self._locators)
        self._dismissal = ModalDismissal(self._locators, page)

    # --- локаторы ---

    @property
    def modal(self):
        return self._locators.modal

    @property
    def continue_btn(self):
        return self._locators.continue_btn

    @property
    def save_and_continue_btn(self):
        return self._locators.save_and_continue_btn

    @property
    def later_btn(self):
        return self._locators.later_btn

    @property
    def close_icon(self):
        return self._locators.close_icon

    @property
    def onboarding_modal_close_btn(self):
        return self._locators.close_icon

    # --- базовые клики ---

    def click_continue(self):
        self.continue_btn.click()

    def click_save_and_continue(self):
        self.save_and_continue_btn.click()

    def click_later_btn(self):
        self.later_btn.click()

    def click_modal_close_button(self) -> None:
        """ТК шаг 7: кнопка закрытия модалки (SVG с aria-label в шапке онбординга)."""
        close_btn = self.close_icon
        expect(close_btn).to_be_visible(timeout=12_000)
        expect(close_btn).to_be_enabled(timeout=5_000)
        close_btn.click(timeout=10_000)

    # --- видимость шагов ---

    def expect_onboarding_visible(self, *, timeout_ms: int = 30_000) -> None:
        self._steps.expect_onboarding_visible(timeout_ms=timeout_ms)

    def expect_progress_fraction(self, current: int, total: int = 5) -> None:
        self._steps.expect_progress_fraction(current, total)

    def expect_onboarding_second_step_visible(self):
        self._steps.expect_second_step_visible()

    def expect_onboarding_third_step_visible(self):
        self._steps.expect_third_step_visible()

    def expect_onboarding_fourth_step_visible(self):
        self._steps.expect_fourth_step_visible()

    def expect_onboarding_fifth_step_visible(self):
        self._steps.expect_fifth_step_visible()

    def expect_onboarding_visible_after_register(self, *, timeout_ms: int = 45_000) -> None:
        """После UI signUp: поллим overlay/modal (SPA на stage рисует онбординг с задержкой)."""
        heading = self.page.get_by_role("heading", name="Onboarding")
        progress_1 = self.page.get_by_text(re.compile(r"1\s*/\s*5|1\s+of\s+5", re.I)).first
        fallback_modal = self.page.locator('[data-testid="Modal"]').filter(has=heading)
        overlay = self.page.get_by_test_id("Modal_Overlay")
        max_rounds = max(1, timeout_ms // 500)
        reloaded = False

        for i in range(max_rounds):
            if self.modal.is_visible(timeout=400):
                self.expect_onboarding_visible(timeout_ms=5_000)
                return
            if fallback_modal.first.is_visible(timeout=400):
                expect(heading).to_be_visible(timeout=5_000)
                expect(progress_1).to_be_visible(timeout=10_000)
                return
            if heading.is_visible(timeout=400) and progress_1.is_visible(timeout=400):
                return
            if overlay.count() and overlay.first.is_visible(timeout=300):
                self.page.wait_for_timeout(500)
                continue
            if i >= 20 and not reloaded:
                self.page.reload(wait_until="domcontentloaded", timeout=60_000)
                reloaded = True
                continue
            self.page.wait_for_timeout(500)

        self.expect_onboarding_visible(timeout_ms=5_000)

    # --- завершение / скрытие ---

    def expect_onboarding_hidden(self, timeout_ms: int = 25_000) -> None:
        self.expect_onboarding_dismissed(timeout_ms=timeout_ms)

    def expect_onboarding_dismissed(self, timeout_ms: int = 30_000) -> None:
        self._dismissal.expect_dismissed(timeout_ms=timeout_ms)

    def close_onboarding_modal(self) -> None:
        """Закрытие модалки: крестик → именованная кнопка → primary CTA → Escape."""
        self._dismissal.dismiss()

    def try_dismiss_with_escape(self, *, presses: int = 3) -> bool:
        """Быстрый путь: Escape, если модалка не обязательна к прохождению всех шагов."""
        return self._dismissal.try_escape(presses=presses)

    def _close_onboarding_if_still_open(self) -> None:
        """Крестик / Escape — без повторного прохода шага 2."""
        if self._dismissal.is_dismissed(timeout_ms=3_000):
            return

        heading = self.page.get_by_role("heading", name="Onboarding")
        if heading.is_visible(timeout=1_000):
            try:
                self.click_modal_close_button()
                self.expect_onboarding_dismissed(timeout_ms=12_000)
                return
            except AssertionError:
                pass

        self.close_onboarding_modal()
        self.expect_onboarding_dismissed()

    def _ensure_onboarding_dismissed(self) -> None:
        """Финальный проход: Escape / close CTA / длинный timeout."""
        if self.modal.is_visible(timeout=2_000) or self.page.get_by_role(
            "heading", name="Onboarding"
        ).is_visible(timeout=1_000):
            self.try_dismiss_with_escape(presses=5)
        if self.modal.is_visible(timeout=1_000) or self.page.get_by_role(
            "heading", name="Onboarding"
        ).is_visible(timeout=1_000):
            self.close_onboarding_modal()
        self.expect_onboarding_dismissed(timeout_ms=45_000)

    # --- шаг 2: специализация ---

    def open_specialization_dropdown(self) -> None:
        self._specialization.open_dropdown()

    def expect_specialization_list_visible(self) -> None:
        self._specialization.expect_list_visible()

    def choose_reference_specialization(self) -> None:
        self._specialization.choose_reference()

    def open_drop_down_and_choose_specialization(self) -> None:
        self._specialization.open_and_choose()

    def _advance_from_specialization_step_if_needed(self) -> None:
        """Шаг 2/5: searchable dropdown — без выбора «Сохранить» не уходит дальше."""
        if not self._locators.specialization_dropdown.is_visible(timeout=2_000):
            return
        self.open_drop_down_and_choose_specialization()
        self.click_save_and_continue()
        if self.continue_btn.is_visible(timeout=8_000):
            self.click_continue()
        if self.later_btn.is_visible(timeout=8_000):
            self.click_later_btn()

    # --- составные сценарии (вызываются из тест-кейсов) ---

    def complete_tc_steps_2_through_7(self) -> None:
        """Шаги модалки 2–7: специализация → сохранить → 3–4 → Позже → 5/5 → крестик.

        Предусловие: уже на шаге 2/5 (выбор специализации).
        """
        self.expect_progress_fraction(2, 5)
        self.expect_onboarding_second_step_visible()
        self.open_drop_down_and_choose_specialization()
        expect(self._locators.specialization_dropdown).to_be_visible()

        self.click_save_and_continue()
        self.expect_progress_fraction(3, 5)
        self.expect_onboarding_third_step_visible()
        self.click_continue()

        self.expect_progress_fraction(4, 5)
        self.expect_onboarding_fourth_step_visible()
        self.click_later_btn()

        self.expect_progress_fraction(5, 5)
        self.expect_onboarding_fifth_step_visible()
        self.complete_onboarding_step_7_close()

    def finish_onboarding_after_fifth_step(self) -> None:
        """ТК 459 шаги 6–7: на 5/5 модалка часто закрывается сама; крестик — только fallback."""
        try:
            self.expect_onboarding_dismissed(timeout_ms=10_000)
            return
        except AssertionError:
            pass

        progress_5 = self.modal.get_by_text(re.compile(r"5\s*/\s*5|5\s+of\s+5", re.I)).first
        if progress_5.is_visible(timeout=3_000):
            self.expect_onboarding_fifth_step_visible()
            primary = self._locators.primary_btn
            if primary.is_visible(timeout=2_000):
                primary.click(timeout=10_000)
            elif self.continue_btn.is_visible(timeout=2_000):
                self.continue_btn.click(timeout=10_000)
            try:
                self.expect_onboarding_dismissed(timeout_ms=10_000)
                return
            except AssertionError:
                pass

        self._close_onboarding_if_still_open()

    def complete_onboarding_step_7_close(self) -> None:
        """ТК шаг 7: крестик; для полного flow после 5/5 предпочтительнее `finish_onboarding_after_fifth_step`."""
        progress_2 = self.modal.get_by_text(re.compile(r"2\s*/\s*5|2\s+of\s+5", re.I)).first
        progress_5 = self.modal.get_by_text(re.compile(r"5\s*/\s*5|5\s+of\s+5", re.I)).first
        if progress_2.is_visible(timeout=1_000) and not progress_5.is_visible(timeout=500):
            self._advance_from_specialization_step_if_needed()

        self._close_onboarding_if_still_open()

    def close_onboarding_at_step_7(self) -> None:
        """Alias для теста ТК 459."""
        self.complete_onboarding_step_7_close()

    def complete_onboarding_through_close(self) -> None:
        """Шаги 1–5: при необходимости «Продолжить» на 1/5 → далее 2–5 и закрытие.

        После долгого API/IMAP UI может остаться на 2-м шаге или уже уйти на 3+,
        поэтому каждый шаг выполняется только если виден его маркер.
        """
        expect(self.modal).to_be_visible(timeout=10_000)

        progress_1 = self.modal.get_by_text(re.compile(r"1\s*/\s*5|1\s+of\s+5", re.I)).first
        if progress_1.is_visible(timeout=3_000) and self.continue_btn.is_visible(timeout=2_000):
            expect(self.continue_btn).to_be_enabled(timeout=5_000)
            self.click_continue()
            expect(
                self.modal.get_by_text(re.compile(r"2\s*/\s*5|2\s+of\s+5", re.I)).first
            ).to_be_visible(timeout=15_000)

        if self._locators.specialization_dropdown.is_visible(timeout=5_000):
            self.open_drop_down_and_choose_specialization()
            self.click_save_and_continue()

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

        try:
            expect(self.modal).to_be_hidden(timeout=5_000)
            return
        except AssertionError:
            pass

        progress_5 = self.modal.get_by_text(re.compile(r"5\s*/\s*5|5\s+of\s+5", re.I)).first
        if progress_5.is_visible(timeout=10_000):
            final_copy = self.modal.get_by_text(
                re.compile(
                    r"YeaHub\s+становится\s+лучше|благодаря\s+вам|становится\s+лучше",
                    re.I,
                )
            ).first
            if not final_copy.is_visible(timeout=3_000):
                expect(self.close_icon).to_be_visible(timeout=12_000)
            else:
                expect(final_copy).to_be_visible(timeout=15_000)

        self.close_onboarding_modal()
        self._ensure_onboarding_dismissed()
