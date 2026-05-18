"""Смена пароля в настройках (desktop), Test IT [113](https://team-vz1y.testit.software/browse/113).

Пользователь: API signUp (`registered_user`), teardown — delete_user. Верификация email не нужна.
Доступ к форме: deep link `/settings#change-password`; при блокировке — снятие онбординга.
"""

import re
from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page, expect

from pages.auth.login_page import LoginPage
from pages.interview.interview_page import InterviewPage
from pages.layout.user_menu import UserMenu
from pages.settings.change_password_page import ChangePasswordPage
from utils.data_generator import DataGenerator


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Settings")
@allure.story("Change password")
@allure.title("Смена пароля в настройках (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "settings")
@testit.workItemIds("2b625597-554c-4ff4-8344-c98b4cf3ab12")
@testit.externalId("yeahub-ui-settings-change-password-desktop-113")
@testit.title("Смена пароля в настройках (desktop)")
def test_change_password_settings_desktop(page: Page, registered_user: dict[str, Any]):
    """Смена пароля: settings → logout → login с новым паролем."""
    email = registered_user["email"]
    current_password = registered_user["password"]
    username = registered_user["username"]
    new_password = DataGenerator.random_password()
    while new_password == current_password:
        new_password = DataGenerator.random_password()

    with allure.step("Предусловие: UI-вход в личный кабинет"):
        login_page = LoginPage(page)
        login_page.open()
        login_page.fill_credentials(email, current_password)
        login_page.submit()
        InterviewPage(page).expect_authorized_after_login(username=username)

    change_password_page = ChangePasswordPage(page)

    with allure.step(
        "Предусловие: /settings#change-password (deep link; онбординг — только если блокирует)"
    ):
        change_password_page.open_change_password_ready()

    with allure.step("Шаги 1–2: новый пароль и повтор без ошибок валидации"):
        change_password_page.fill_new_password(new_password)
        change_password_page.fill_confirm_password(new_password)
        change_password_page.expect_no_validation_errors()
        change_password_page.expect_save_enabled()

    with allure.step("Шаг 3: «Сохранить» → тост успеха, поля очищены, кнопка неактивна"):
        change_password_page.click_save()
        change_password_page.expect_success_notification()
        change_password_page.expect_form_reset_after_success()
        registered_user["active_password"] = new_password

    with allure.step("Шаги 4–5: меню профиля → «Выйти» → /auth/login"):
        UserMenu(page).logout_via_profile_menu()
        expect(page).to_have_url(re.compile(r".*/auth/login", re.I), timeout=20_000)

    with allure.step("Шаг 6: вход с новым паролем → /interview"):
        login_page = LoginPage(page)
        login_page.expect_login_form_elements_visible()
        login_page.fill_credentials(email, new_password)
        login_page.submit()
        InterviewPage(page).expect_authorized_after_login(username=username)
