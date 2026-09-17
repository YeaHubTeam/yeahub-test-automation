import re

from playwright.sync_api import expect


class StepVisibility:
    """Ассерты видимости конкретных шагов онбординга и прогресс-бара.

    Единственная ответственность — проверить, что нужный шаг на экране.
    Никаких кликов и переходов между шагами здесь.
    """

    def __init__(self, locators):
        self._loc = locators

    def expect_onboarding_visible(self, *, timeout_ms: int = 30_000) -> None:
        expect(self._loc.modal).to_be_visible(timeout=timeout_ms)
        expect(self._loc.modal.get_by_test_id("stepper")).to_be_visible(timeout=timeout_ms)
        expect(self._loc.modal.get_by_role("heading", name="Onboarding")).to_be_visible(
            timeout=timeout_ms
        )

    def expect_progress_fraction(self, current: int, total: int = 5) -> None:
        """Этап n/m на прогресс-баре онбординга (допускаем пробелы вокруг «/»)."""
        expect(self._loc.modal.get_by_text(re.compile(rf"{current}\s*/\s*{total}"))).to_be_visible()

    def expect_second_step_visible(self):
        """Шаг 2: якорь `dropdown-select`; заголовок — «Выбери свою специализацию» (не role=heading).

        Не матчим голое «специализац» — на экране ещё подпись «Выбор специализации», плейсхолдер.
        """
        expect(self._loc.specialization_dropdown).to_be_visible(timeout=15_000)
        expect(
            self._loc.modal.get_by_text(
                re.compile(
                    r"Выбери\s+свою\s+специализац"
                    r"|Выберите\s+свою\s+специализац"
                    r"|Choose\s+your\s+speciali",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=10_000)

    def expect_third_step_visible(self):
        """Копирайт шага 3 часто не в role=heading."""
        expect(
            self._loc.modal.get_by_text(
                re.compile(
                    r"Сейчас на платформе|сервис для подготовки|подготовк.*собеседован",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=15_000)
        expect(self._loc.continue_btn).to_be_visible(timeout=10_000)

    def expect_fourth_step_visible(self):
        """Шаг 4: «Позже» + любой узнаваемый фрагмент экрана про подписку/развитие."""
        expect(self._loc.later_btn).to_be_visible(timeout=15_000)
        expect(
            self._loc.modal.get_by_text(
                re.compile(
                    r"подписк|развива.*платформ|subscription|membership",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=10_000)

    def expect_fifth_step_visible(self):
        expect(
            self._loc.modal.get_by_text(
                re.compile(
                    r"YeaHub\s+становится\s+лучше|благодаря\s+вам|становится\s+лучше",
                    re.I,
                )
            ).first
        ).to_be_visible(timeout=15_000)
