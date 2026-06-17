import re

from playwright.sync_api import expect

_DELETE_BTN = re.compile(r"^Удалить\s+аккаунт$|^Delete\s+account$", re.I)
_CANCEL_BTN = re.compile(r"^Отменить$|^Cancel$", re.I)
_IRREVERSIBLE_WARNING = re.compile(
    r"необратим|нельзя\s+восстанов|восстановлен|безвозврат|"
    r"cannot\s+be\s+undone|irrevers|"
    r"введите.*никнейм|введите\s+свой\s+ник|enter\s+your\s+nick|"
    r"подтверд.*удал|удал.*данн",
    re.I,
)


class DeleteAccountModal:
    """Модалка подтверждения удаления аккаунта (Настройки → Аккаунт)."""

    def __init__(self, page):
        self.page = page
        self._modal = page.locator('[data-testid="Modal"]').filter(has_text="Удаление аккаунта")

    @property
    def modal(self):
        return self._modal

    @property
    def nickname_input(self):
        return self.modal.get_by_test_id("Input_Field")

    @property
    def confirm_button(self):
        return self.modal.get_by_test_id("Modal_Primary_Button")

    @property
    def cancel_button(self):
        return self.modal.get_by_test_id("Modal_Outline_Button")

    @property
    def close_button(self):
        return self.modal.get_by_test_id("Modal_Close_Icon")

    def expect_visible(self):
        expect(self.modal).to_be_visible()
        expect(self.modal.get_by_test_id("Modal_Title")).to_have_text("Удаление аккаунта")

    def expect_confirmation_dialog_content(self) -> None:
        """ТК 117 шаг 2: заголовок, предупреждение, поле никнейма, кнопки."""
        self.expect_visible()
        expect(self.modal.get_by_text(_IRREVERSIBLE_WARNING).first).to_be_visible(timeout=10_000)
        expect(self.nickname_input).to_be_visible(timeout=10_000)
        expect(self.confirm_button).to_be_visible(timeout=10_000)
        expect(self.confirm_button).to_contain_text(_DELETE_BTN, timeout=10_000)
        expect(self.cancel_button).to_be_visible(timeout=10_000)
        expect(self.cancel_button).to_contain_text(_CANCEL_BTN, timeout=10_000)

    def expect_confirm_delete_disabled(self) -> None:
        expect(self.confirm_button).to_be_disabled(timeout=10_000)

    def fill_confirmation_nickname(self, username: str) -> None:
        self.nickname_input.fill(username)

    def expect_confirm_delete_enabled(self) -> None:
        expect(self.confirm_button).to_be_enabled(timeout=10_000)

    def confirm_delete(self) -> None:
        expect(self.confirm_button).to_be_enabled(timeout=10_000)
        self.confirm_button.click()

    def cancel(self) -> None:
        self.cancel_button.click()

    def close(self) -> None:
        self.close_button.click()

    def expect_hidden(self):
        expect(self.modal).to_be_hidden()

    def expect_redirect_to_register(self):
        expect(self.page).to_have_url(re.compile(r".*/auth/register"))

    def expect_account_deleted_toast(self):
        expect(
            self.page.get_by_text(re.compile(r"удал|успеш|deleted|success", re.I)).first
        ).to_be_visible(timeout=10_000)
