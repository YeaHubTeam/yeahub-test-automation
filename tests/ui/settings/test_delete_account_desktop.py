"""Удаление аккаунта из настроек (desktop), Test IT [117](https://team-vz1y.testit.software/browse/117).

Пользователь: API signUp (`registered_user`), удаление через UI — teardown delete_user no-op при auth_failed.
"""

from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from pages.auth.login_page import LoginPage
from pages.auth.register_page import RegisterPage
from pages.interview.interview_page import INTERVIEW_URL_RE, InterviewPage
from pages.settings.settings_page import SettingsPage
from utils.reporting import report_step


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Settings")
@allure.story("Delete account")
@allure.title("Удаление аккаунта из настроек аккаунта (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "settings")
@testit.workItemIds("1dfd896e-1a4c-468a-8c2d-cc33283666bb")
@testit.externalId("yeahub-ui-settings-delete-account-desktop-117")
@testit.title("Удаление аккаунта из настроек аккаунта (desktop)")
@testit.description(
    "ТК 117: registered_user → UI login → /settings#account → модалка удаления → "
    "/auth/register → login → ошибка входа для удалённого пользователя."
)
def test_delete_account_from_settings_desktop(page: Page, registered_user: dict[str, Any]):
    email = registered_user["email"]
    password = registered_user["password"]
    username = registered_user["username"]

    login_page = LoginPage(page)
    interview_page = InterviewPage(page)
    settings_page = SettingsPage(page)
    register_page = RegisterPage(page)
    modal = settings_page.delete_account_modal

    with report_step(
        "Предусловие 1: зарегистрированный пользователь с известными email, паролем и никнеймом",
        "fixture registered_user: API signUp 201",
    ):
        pass

    with report_step(
        "Предусловие 2: авторизация и /settings#account",
        "Вкладка «Аккаунт», блок «Удаление аккаунта» с кнопкой «Удалить аккаунт»",
    ):
        login_page.open()
        login_page.fill_credentials(email, password)
        login_page.submit_expecting_success()
        if not INTERVIEW_URL_RE.search(page.url):
            interview_page.open_interview()
        interview_page.expect_authorized_after_login(username=username, email=email)
        interview_page.prepare_interview_after_login()
        interview_page.ensure_onboarding_completed_before_settings()
        settings_page.open_account_ready()
        settings_page.expect_delete_account_section_visible()

    with report_step(
        "Шаг 1: «Удалить аккаунт» в блоке «Удаление аккаунта»",
        "Открывается модальное окно подтверждения удаления",
    ):
        settings_page.open_delete_account_modal()

    with report_step(
        "Шаг 2: содержимое модального окна",
        "Заголовок, предупреждение, поле никнейма, «Удалить аккаунт», «Отменить»",
    ):
        modal.expect_confirmation_dialog_content()

    with report_step(
        "Шаг 3: без ввода никнейма кнопка «Удалить аккаунт» неактивна",
        "Primary-кнопка в модалке disabled",
    ):
        modal.expect_confirm_delete_disabled()

    with report_step(
        "Шаг 4: ввести никнейм текущего пользователя",
        "Кнопка «Удалить аккаунт» становится активной",
    ):
        modal.fill_confirmation_nickname(username)
        modal.expect_confirm_delete_enabled()

    with report_step(
        "Шаг 5: «Удалить аккаунт» в модалке",
        "Аккаунт удалён, тост, редирект на /auth/register",
    ):
        modal.confirm_delete()
        modal.expect_account_deleted_toast()
        modal.expect_redirect_to_register()

    with report_step(
        "Шаг 6: на /auth/register «Войти» в блоке «Уже есть аккаунт?»",
        "Переход на /auth/login",
    ):
        register_page.click_login_link()

    with report_step(
        "Шаг 7: вход с учётными данными удалённого пользователя",
        "Авторизация не выполняется: HTTP 401/403, остаёмся на /auth/login",
    ):
        login_page.expect_login_form_elements_visible()
        login_page.fill_credentials(email, password)
        login_page.submit_expecting_unauthorized()
