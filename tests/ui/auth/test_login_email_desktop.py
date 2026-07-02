"""Авторизация по email и паролю (desktop), Test IT [409](https://team-vz1y.testit.software/browse/409).

Предусловия 1–3 и шаги 1–4 по ручному ТК 409.
Пользователь: API signUp (`registered_user`), teardown — delete_user.
Постусловие РК (UI «Выйти») — не в этом автотесте (см. `tests/auth/test_auth_logout.py`).
"""

from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from pages.auth.login_page import LoginPage
from utils.reporting import report_step


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
@testit.description(
    "Ручной ТК 409: предусловия 1–3, шаги 1–4. UI /auth/login → /interview. "
    "Пользователь: registered_user (API signUp). "
    "Постусловие РК (UI «Выйти») — не в этом автотесте; teardown: delete_user."
)
def test_login_with_email_and_password_desktop(page: Page, registered_user: dict[str, Any]):
    """Вход по email и паролю (desktop)."""
    email = registered_user["email"]
    password = registered_user["password"]
    username = registered_user["username"]

    login_page = LoginPage(page)

    with report_step(
        "Предусловие 1: пользователь зарегистрирован по email с валидным паролем",
        "Пользователь может использовать email и пароль для авторизации (fixture registered_user: signUp 201)",
    ):
        pass

    with report_step(
        "Предусловие 2: пользователь не авторизован в системе",
        "У пользователя отсутствует активная сессия (новый браузерный контекст, без UI-входа)",
    ):
        pass

    with report_step(
        "Предусловие 3: открыта страница авторизации /auth/login",
        "Отображается форма авторизации",
    ):
        login_page.open()

    with report_step(
        "Шаг 1: проверить элементы формы авторизации",
        "Отображаются: заголовок «Вход в личный кабинет», поле «Электронная почта», поле «Пароль», "
        "иконка отображения пароля, ссылка «Забыли пароль?», кнопка «Вход», ссылка «Зарегистрироваться»",
    ):
        login_page.expect_login_form_elements_visible()

    with report_step(
        "Шаг 2: ввести в поле «Электронная почта» валидный email пользователя",
        "Значение введено, ошибка валидации не отображается",
    ):
        login_page.page.locator('input[name="username"]').fill(email)
        login_page.expect_no_login_validation_errors()

    with report_step(
        "Шаг 3: ввести в поле «Пароль» валидный пароль пользователя",
        "Значение введено, ошибка валидации не отображается",
    ):
        login_page.page.locator('input[type="password"]').fill(password)
        login_page.expect_no_login_validation_errors()

    with report_step(
        "Шаг 4: нажать кнопку «Вход»",
        "Пользователь успешно авторизован, выполнен переход на страницу /interview",
    ):
        login_page.login_expecting_authorized(email, password, username=username)
