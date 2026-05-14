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

    def expect_progress_fraction(self, current: int, total: int = 5) -> None:
        """Этап n/m на прогресс-баре онбординга (допускаем пробелы вокруг «/»)."""
        expect(self.modal.get_by_text(re.compile(rf"{current}\s*/\s*{total}"))).to_be_visible()

    def expect_onboarding_hidden(self, timeout_ms: int = 25_000) -> None:
        expect(self.modal).to_be_hidden(timeout=timeout_ms)

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

    def choose_qa_engineer_specialization(self) -> None:
        self.page.get_by_role("option", name=re.compile(r"qa\s*engineer", re.I)).click()

    def open_drop_down_and_choose_specialization(self):
        self.open_specialization_dropdown()
        self.choose_qa_engineer_specialization()

    def complete_tc_steps_2_through_7(self) -> None:
        """Шаги модалки 2–7: специализация → сохранить → 3–4 → Позже → 5/5 → крестик.

        Предусловие: уже на шаге 2/5 (выбор специализации).
        """
        self.expect_progress_fraction(2, 5)
        self.expect_onboarding_second_step_visible()
        self.open_specialization_dropdown()
        self.expect_specialization_list_visible()
        self.choose_qa_engineer_specialization()
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
        self.close_onboarding_modal()
        self.expect_onboarding_hidden()

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
        """Закрытие последнего шага: явная CTA / primary из дизайн-системы → крестик → Escape.

        На prod часто меняют приоритет кнопки vs крестика; один только X может не срабатывать
        (оверлей, pointer-events), поэтому дублируем путь как у других модалок (`Modal_Primary_Button`).
        """
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

        icon = self.close_icon
        icon.scroll_into_view_if_needed()
        icon.wait_for(state="visible", timeout=15_000)
        icon.click(timeout=10_000, force=True)
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
        expect(self.modal).to_be_hidden(timeout=25_000)
