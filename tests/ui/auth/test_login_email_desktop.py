"""Авторизация по email и паролю (desktop), Test IT [409](https://team-vz1y.testit.software/browse/409).

Автотест покрывает шаги 1–4 (форма, ввод, «Вход», /interview).
Постусловие «Выйти» (UI) — onboarding e2e / API logout; teardown — `registered_user` → delete_user.
"""

from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from pages.auth.login_page import LoginPage
from pages.interview.interview_page import InterviewPage


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Login")
@allure.title("Вход по email и паролю (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "auth")
@testit.workItemIds("03f79540-7ecf-4736-8a98-77ba1d606aef")
@testit.externalId("yeahub-ui-auth-login-email-password-desktop-409")
@testit.title("Вход по email и паролю (desktop)")
def test_login_with_email_and_password_desktop(page: Page, registered_user: dict[str, Any]):
    """Вход по email и паролю (desktop)."""
    email = registered_user["email"]
    password = registered_user["password"]
    username = registered_user["username"]

    with allure.step("Предусловие: открыта страница /auth/login"):
        login_page = LoginPage(page)
        login_page.open()

    with allure.step("Шаг 1: проверить элементы формы авторизации"):
        login_page.expect_login_form_elements_visible()

    with allure.step("Шаги 2–3: ввести email и пароль без ошибок валидации"):
        login_page.fill_credentials(email, password)
        login_page.expect_no_login_validation_errors()

    with allure.step("Шаг 4: «Вход» → авторизация и переход на /interview"):
        login_page.submit()
        InterviewPage(page).expect_authorized_after_login(username=username)
