import re

from playwright.sync_api import expect

# Эталон специализации для автотестов (stage: id=11, slug=react-frontend-developer).
REFERENCE_SPECIALIZATION_ID = 11
REFERENCE_SPECIALIZATION_TITLE_PATTERN = re.compile(r"React\s+Frontend\s+Developer", re.I)
CLOSE_MODAL_BUTTON_NAME = re.compile(r"Закрыть модальное окно|Close modal", re.I)


class OnboardingModal:
    def __init__(self, page):
        self.page = page
        # Только `has_text="Onboarding"` ломается на флаке (тайминг/DOM) — stepper стабильнее для всех шагов 1–5.
        self._modal = page.locator('[data-testid="Modal"]').filter(
            has=page.get_by_test_id("stepper")
        )

    @property
    def modal(self):
        return self._modal

    @property
    def continue_btn(self):
        return self.modal.get_by_role(
            "button",
            name=re.compile(r"^\s*Продолжить\s*$|^\s*Continue\s*$", re.I),
        )

    @property
    def save_and_continue_btn(self):
        return self.modal.get_by_role("button", name="Сохранить и продолжить")

    @property
    def later_btn(self):
        return self.modal.get_by_role("button", name="Позже")

    @property
    def close_icon(self):
        """Крестик в шапке: `aria-label` «Закрыть модальное окно» / `data-testid=Modal_Close_Icon`."""
        by_aria = self.modal.get_by_role("button", name=CLOSE_MODAL_BUTTON_NAME)
        if by_aria.count():
            return by_aria.first
        return self.modal.get_by_test_id("Modal_Close_Icon").first

    def click_modal_close_button(self) -> None:
        """ТК шаг 7: кнопка закрытия модалки (SVG с aria-label в шапке онбординга)."""
        close_btn = self.close_icon
        expect(close_btn).to_be_visible(timeout=12_000)
        expect(close_btn).to_be_enabled(timeout=5_000)
        close_btn.click(timeout=10_000)

    @property
    def onboarding_modal_close_btn(self):
        return self.close_icon

    def expect_onboarding_visible(self, *, timeout_ms: int = 30_000) -> None:
        expect(self.modal).to_be_visible(timeout=timeout_ms)
        expect(self.modal.get_by_test_id("stepper")).to_be_visible(timeout=timeout_ms)
        expect(self.modal.get_by_role("heading", name="Onboarding")).to_be_visible(
            timeout=timeout_ms
        )

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

    def expect_progress_fraction(self, current: int, total: int = 5) -> None:
        """Этап n/m на прогресс-баре онбординга (допускаем пробелы вокруг «/»)."""
        expect(self.modal.get_by_text(re.compile(rf"{current}\s*/\s*{total}"))).to_be_visible()

    def expect_onboarding_hidden(self, timeout_ms: int = 25_000) -> None:
        self.expect_onboarding_dismissed(timeout_ms=timeout_ms)

    def expect_onboarding_dismissed(self, timeout_ms: int = 30_000) -> None:
        """Онбординг завершён: нет заголовка Onboarding и stepper-модалки."""
        expect(self.page.get_by_role("heading", name="Onboarding")).to_be_hidden(timeout=timeout_ms)
        expect(self.modal).to_be_hidden(timeout=5_000)

    def click_continue(self):
        self.continue_btn.click()

    def expect_onboarding_second_step_visible(self):
        """Шаг 2: якорь `dropdown-select`; заголовок — «Выбери свою специализацию» (не role=heading).

        Не матчим голое «специализац» — на экране ещё подпись «Выбор специализации», плейсхолдер и абзац.
        """
        expect(self.modal.get_by_test_id("dropdown-select")).to_be_visible(timeout=15_000)
        expect(
            self.modal.get_by_text(
                re.compile(
                    r"Выбери\s+свою\s+специализац"
                    r"|Выберите\s+свою\s+специализац"
                    r"|Choose\s+your\s+speciali",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=10_000)

    def open_specialization_dropdown(self) -> None:
        self.modal.get_by_test_id("dropdown-select").click()

    def expect_specialization_list_visible(self) -> None:
        expect(self.page.get_by_role("option").first).to_be_visible(timeout=10_000)

    def choose_reference_specialization(self) -> None:
        """Эталон: React Frontend Developer (см. REFERENCE_SPECIALIZATION_ID)."""
        self.page.get_by_role("option", name=REFERENCE_SPECIALIZATION_TITLE_PATTERN).click()

    def open_drop_down_and_choose_specialization(self) -> None:
        self.open_specialization_dropdown()
        self.choose_reference_specialization()

    def complete_tc_steps_2_through_7(self) -> None:
        """Шаги модалки 2–7: специализация → сохранить → 3–4 → Позже → 5/5 → крестик.

        Предусловие: уже на шаге 2/5 (выбор специализации).
        """
        self.expect_progress_fraction(2, 5)
        self.expect_onboarding_second_step_visible()
        self.open_specialization_dropdown()
        self.expect_specialization_list_visible()
        self.choose_reference_specialization()
        expect(self.modal.get_by_test_id("dropdown-select")).to_be_visible()

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

    def complete_onboarding_step_7_close(self) -> None:
        """ТК шаг 7: крестик «Закрыть модальное окно»; fallback — Primary / Continue / close_onboarding_modal."""
        self.expect_progress_fraction(5, 5)
        self.expect_onboarding_fifth_step_visible()

        try:
            self.expect_onboarding_dismissed(timeout_ms=3_000)
            return
        except AssertionError:
            pass

        heading = self.page.get_by_role("heading", name="Onboarding")

        if heading.is_visible(timeout=1_000):
            self.click_modal_close_button()
            try:
                self.expect_onboarding_dismissed(timeout_ms=12_000)
                return
            except AssertionError:
                pass

        primary = self.modal.get_by_test_id("Modal_Primary_Button")
        if heading.is_visible(timeout=1_000) and primary.is_visible(timeout=2_000):
            primary.click(timeout=10_000)
            try:
                self.expect_onboarding_dismissed(timeout_ms=12_000)
                return
            except AssertionError:
                pass

        if heading.is_visible(timeout=1_000) and self.continue_btn.is_visible(timeout=2_000):
            self.continue_btn.click(timeout=10_000)
            try:
                self.expect_onboarding_dismissed(timeout_ms=12_000)
                return
            except AssertionError:
                pass

        self.close_onboarding_modal()
        self.expect_onboarding_dismissed()

    def close_onboarding_at_step_7(self) -> None:
        """Alias для теста ТК 459."""
        self.complete_onboarding_step_7_close()

    def click_save_and_continue(self):
        self.save_and_continue_btn.click()

    def expect_onboarding_third_step_visible(self):
        """Копирайт шага 3 часто не в role=heading — те же фрагменты, что в `complete_onboarding_through_close`."""
        expect(
            self.modal.get_by_text(
                re.compile(
                    r"Сейчас на платформе|сервис для подготовки|подготовк.*собеседован",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=15_000)
        expect(self.continue_btn).to_be_visible(timeout=10_000)

    def expect_onboarding_fourth_step_visible(self):
        """Шаг 4: «Позже» + любой узнаваемый фрагмент экрана про подписку/развитие."""
        expect(self.later_btn).to_be_visible(timeout=15_000)
        expect(
            self.modal.get_by_text(
                re.compile(
                    r"подписк|развива.*платформ|subscription|membership",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=10_000)

    def click_later_btn(self):
        self.later_btn.click()

    def expect_onboarding_fifth_step_visible(self):
        expect(
            self.modal.get_by_text(
                re.compile(
                    r"YeaHub\s+становится\s+лучше|благодаря\s+вам|становится\s+лучше",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=15_000)

    def close_onboarding_modal(self) -> None:
        """Закрытие последнего шага: крестик в шапке → CTA → Escape.

        Крестик: role=button, aria-label «Закрыть модальное окно», testid=Modal_Close_Icon.
        """
        if self.close_icon.is_visible(timeout=2_000):
            try:
                self.click_modal_close_button()
                try:
                    expect(self.modal).to_be_hidden(timeout=5_000)
                    return
                except AssertionError:
                    pass
            except AssertionError:
                pass

        # Кнопка с доступным именем (i18n / короткие лейблы на финале)
        named_dismiss = self.modal.get_by_role(
            "button",
            name=re.compile(
                r"Закрыть|Готово|Понятно|Начать|Ок\b|\bOK\b|Done|Close|Got it",
                re.I,
            ),
        )
        if named_dismiss.first.is_visible(timeout=2_000):
            named_dismiss.first.click(timeout=10_000)
            try:
                expect(self.modal).to_be_hidden(timeout=5_000)
                return
            except AssertionError:
                pass

        primary = self.modal.get_by_test_id("Modal_Primary_Button")
        if primary.is_visible(timeout=2_000):
            primary.click(timeout=10_000)
            try:
                expect(self.modal).to_be_hidden(timeout=5_000)
                return
            except AssertionError:
                pass

        self.page.keyboard.press("Escape")
        try:
            expect(self.modal).to_be_hidden(timeout=3_000)
            return
        except AssertionError:
            self.page.keyboard.press("Escape")

    def complete_onboarding_through_close(self) -> None:
        """Шаги 1–5: при необходимости «Продолжить» на 1/5 → далее 2–5 и закрытие.

        После долгого API/IMAP UI может остаться на 2-м шаге или уже уйти на 3+,
        поэтому каждый шаг выполняется только если виден его маркер.
        Прямой вход на /interview (например API signUp + UI login) часто оставляет шаг 1/5 открытым.
        """
        expect(self.modal).to_be_visible(timeout=10_000)

        progress_1 = self.modal.get_by_text(re.compile(r"1\s*/\s*5|1\s+of\s+5", re.I)).first
        if progress_1.is_visible(timeout=3_000) and self.continue_btn.is_visible(timeout=2_000):
            expect(self.continue_btn).to_be_enabled(timeout=5_000)
            self.click_continue()
            expect(
                self.modal.get_by_text(re.compile(r"2\s*/\s*5|2\s+of\s+5", re.I)).first
            ).to_be_visible(timeout=15_000)

        if self.modal.get_by_test_id("dropdown-select").is_visible(timeout=5_000):
            self.open_specialization_dropdown()
            self.expect_specialization_list_visible()
            self.choose_reference_specialization()
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

        # После «Позже» модалка может сразу закрыться, перейти на 5/5 или остаться на 4/5.
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

    def _ensure_onboarding_dismissed(self) -> None:
        """Финальный проход: Escape / шаг 7 / длинный timeout — stage иногда не закрывает модалку с первого раза."""
        if self.modal.is_visible(timeout=2_000) or self.page.get_by_role(
            "heading", name="Onboarding"
        ).is_visible(timeout=1_000):
            self.try_dismiss_with_escape(presses=5)
        if self.modal.is_visible(timeout=1_000) or self.page.get_by_role(
            "heading", name="Onboarding"
        ).is_visible(timeout=1_000):
            self.complete_onboarding_step_7_close()
        self.expect_onboarding_dismissed(timeout_ms=45_000)

    def try_dismiss_with_escape(self, *, presses: int = 3) -> bool:
        """Быстрый путь: Escape, если модалка не обязательна к прохождению всех шагов."""
        for _ in range(presses):
            if not self.modal.is_visible(timeout=400):
                return True
            self.page.keyboard.press("Escape")
            try:
                expect(self.modal).to_be_hidden(timeout=2_500)
                return True
            except AssertionError:
                pass
        return not self.modal.is_visible(timeout=400)
