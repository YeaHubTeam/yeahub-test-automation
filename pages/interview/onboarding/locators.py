import re

CLOSE_MODAL_BUTTON_NAME = re.compile(r"Закрыть модальное окно|Close modal", re.I)


class OnboardingLocators:
    """Локаторы модалки онбординга и её элементов управления.

    Единственная ответственность — найти элемент. Никаких expect/click здесь.
    """

    def __init__(self, page):
        self.page = page
        # Только `has_text="Onboarding"` ломается на флаке (тайминг/DOM) — stepper стабильнее.
        self.modal = page.locator('[data-testid="Modal"]').filter(
            has=page.get_by_test_id("stepper")
        )

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

    @property
    def primary_btn(self):
        return self.modal.get_by_test_id("Modal_Primary_Button")

    @property
    def specialization_dropdown(self):
        return self.modal.get_by_test_id("dropdown-select")

    @property
    def specialization_listbox(self):
        """Список рендерится в portaled listbox вне modal — не матчим скрытые option по всей странице."""
        return self.page.get_by_role("listbox").last

    def specialization_options(self):
        listbox = self.specialization_listbox
        if listbox.count() and listbox.is_visible(timeout=300):
            return listbox.get_by_role("option")
        return self.page.get_by_role("option")
