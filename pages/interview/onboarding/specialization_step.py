import re

from playwright.sync_api import expect

# Эталон специализации для автотестов (stage: id=11, slug=react-frontend-developer).
REFERENCE_SPECIALIZATION_ID = 11
REFERENCE_SPECIALIZATION_TITLE_PATTERN = re.compile(r"React\s+Frontend\s+Developer", re.I)


class SpecializationStep:
    """Шаг 2 онбординга: выбор специализации в searchable dropdown.

    Единственная ответственность — открыть/закрыть/выбрать в этом конкретном dropdown.
    """

    def __init__(self, locators):
        self._loc = locators

    def _is_dropdown_open(self) -> bool:
        expanded = self._loc.specialization_dropdown.get_attribute("aria-expanded")
        if expanded == "true":
            return True
        listbox = self._loc.specialization_listbox
        return listbox.count() > 0 and listbox.is_visible(timeout=200)

    def _expect_listbox_open(self, *, timeout_ms: int = 15_000) -> None:
        expect(self._loc.specialization_listbox).to_be_visible(timeout=timeout_ms)
        expect(self._loc.specialization_options().first).to_be_visible(timeout=timeout_ms)

    def open_dropdown(self) -> None:
        """`dropdown-select` — toggle; повторный click только если список ещё закрыт."""
        dropdown = self._loc.specialization_dropdown
        expect(dropdown).to_be_visible(timeout=15_000)
        dropdown.scroll_into_view_if_needed(timeout=5_000)
        if self._is_dropdown_open():
            self._expect_listbox_open(timeout_ms=5_000)
            return

        dropdown.click(timeout=10_000)
        try:
            self._expect_listbox_open(timeout_ms=8_000)
            return
        except AssertionError:
            pass

        if not self._is_dropdown_open():
            dropdown.click(timeout=10_000)
            try:
                self._expect_listbox_open(timeout_ms=8_000)
                return
            except AssertionError:
                pass

        dropdown.focus()
        self._loc.page.keyboard.press("ArrowDown")
        self._expect_listbox_open(timeout_ms=15_000)

    def expect_list_visible(self) -> None:
        if self._is_dropdown_open():
            self._expect_listbox_open(timeout_ms=5_000)
            return
        self.open_dropdown()

    def choose_reference(self) -> None:
        """Эталон: React Frontend Developer — option внутри listbox после click на dropdown-select."""
        if not self._is_dropdown_open():
            self.open_dropdown()
        option = self._loc.specialization_options().filter(
            has_text=REFERENCE_SPECIALIZATION_TITLE_PATTERN
        )
        expect(option.first).to_be_visible(timeout=15_000)
        option.first.click()
        expect(self._loc.specialization_dropdown).to_contain_text(
            REFERENCE_SPECIALIZATION_TITLE_PATTERN,
            timeout=10_000,
        )

    def open_and_choose(self) -> None:
        self.open_dropdown()
        self.expect_list_visible()
        self.choose_reference()
