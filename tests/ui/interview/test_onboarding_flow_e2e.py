"""Онбординг после регистрации (desktop), Test IT [459](https://team-vz1y.testit.software/browse/459).

Предусловия: API signUp (`registered_user`) + UI login → /interview, модалка 1/5.
Шаги 1–7: онбординг до закрытия модалки. Специализация — эталон React Frontend Developer.
Teardown: удаление пользователя через fixture `registered_user`.
"""

from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from pages.auth.login_page import LoginPage
from pages.interview.interview_page import InterviewPage
from utils.reporting import report_step


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Interview")
@allure.story("Onboarding")
@allure.title("Онбординг после регистрации (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "interview")
@testit.workItemIds("608dd8ae-b3fa-4103-a9db-2b86c3cbe5ef")
@testit.externalId("yeahub-ui-interview-onboarding-after-register-desktop-459")
@testit.title("Онбординг после регистрации (desktop)")
@testit.description(
    "Ручной ТК 459: предусловия API signUp + UI login; шаги 1–7 онбординга. "
    "Специализация: React Frontend Developer (id=11). "
    "Teardown: registered_user → delete_user. Verify email — отдельные mail-тесты."
)
def test_onboarding_after_register_desktop(page: Page, registered_user: dict[str, Any]):
    """Онбординг после регистрации (desktop)."""
    email = registered_user["email"]
    password = registered_user["password"]
    username = registered_user["username"]

    login_page = LoginPage(page)
    interview_page = InterviewPage(page)
    onboarding = interview_page.onboarding

    with report_step(
        "Предусловие 1–2: пользователь зарегистрирован (API), вход → /interview",
        "signUp 201 (fixture registered_user); после входа URL /interview, пользователь авторизован",
    ):
        login_page.open()
        login_page.fill_credentials(email, password)
        login_page.submit()
        interview_page.expect_authorized_after_login(username=username)

    with report_step(
        "Предусловие 3: модалка онбординга, этап «Приветствие» (1/5)",
        "Модалка Onboarding видна; прогресс 1/5; пользователь ранее не проходил онбординг",
    ):
        onboarding.expect_onboarding_visible()
        onboarding.expect_progress_fraction(1, 5)

    with report_step(
        "Шаг 1: «Продолжить» на «Приветствие»",
        "Прогресс 2/5; экран «Выбор специализации» (dropdown-select, текст про специализацию)",
    ):
        onboarding.click_continue()
        onboarding.expect_progress_fraction(2, 5)
        onboarding.expect_onboarding_second_step_visible()

    with report_step(
        "Шаг 2: открыть список «Выберите специализацию»",
        "Открыт выпадающий список; виден хотя бы один вариант специализации (role=option)",
    ):
        onboarding.open_specialization_dropdown()
        onboarding.expect_specialization_list_visible()

    with report_step(
        "Шаг 3: выбрать специализацию (эталон: React Frontend Developer)",
        "В поле выбрана специализация React Frontend Developer (id=11)",
    ):
        onboarding.choose_reference_specialization()

    with report_step(
        "Шаг 4: «Сохранить и продолжить»",
        "Прогресс 3/5; экран «Подготовка к собеседованиям»; кнопка «Продолжить» видна",
    ):
        onboarding.click_save_and_continue()
        onboarding.expect_progress_fraction(3, 5)
        onboarding.expect_onboarding_third_step_visible()

    with report_step(
        "Шаг 5: «Продолжить»",
        "Прогресс 4/5; экран про подписку/развитие; кнопки «Поддержать» и «Позже» видны",
    ):
        onboarding.click_continue()
        onboarding.expect_progress_fraction(4, 5)
        onboarding.expect_onboarding_fourth_step_visible()

    with report_step(
        "Шаг 6: «Позже»",
        "Прогресс 5/5; финальный экран («YeaHub становится лучше» / благодарность)",
    ):
        onboarding.click_later_btn()
        onboarding.expect_progress_fraction(5, 5)
        onboarding.expect_onboarding_fifth_step_visible()

    with report_step(
        "Шаг 7: закрыть модалку (крестик)",
        "Модалка онбординга закрыта; URL /interview; заголовок Onboarding и stepper скрыты",
    ):
        onboarding.complete_onboarding_step_7_close()
        interview_page.expect_on_interview_route()
