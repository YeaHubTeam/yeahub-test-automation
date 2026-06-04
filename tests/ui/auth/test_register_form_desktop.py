"""Регистрация по email (desktop): форма и submit до onboarding.

Ручной кейс Test IT: workItem `519e37ac-bda7-45c1-aebc-683755c6ecbd`.
Покрывает шаги 1–9 (форма, согласия, редирект на /interview, модалка Onboarding).
Письмо Verify Your Email — ТК 422 (`test_email_verify_desktop`) или полный e2e (`test_register_and_verify_email_e2e`).

Teardown: удаление пользователя через API.

Email: `MAIL_EMAIL` + tag (как register/mail e2e), не faker — письма Verify попадают в тестовый ящик.
"""

import re

import allure
import pytest
import testit
from playwright.sync_api import Page, expect

from api.api_manager import ApiManager
from pages.auth.register_page import RegisterPage
from pages.interview.interview_page import InterviewPage
from tests.mail.verification_flow import delete_authenticated_user_via_api
from tests.ui.flows.register_mail_interview_flow import new_plus_tagged_email
from utils.reporting import report_step


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Register")
@allure.title("Регистрация: форма, согласия, переход на interview (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "auth")
@testit.workItemIds("519e37ac-bda7-45c1-aebc-683755c6ecbd")
@testit.externalId("yeahub-ui-auth-register-form-desktop")
@testit.title("Регистрация: форма, согласия, переход на interview (desktop)")
@testit.description(
    "Ручной ТК: шаги 1–9. UI /auth/register → согласия → /interview, модалка Onboarding. "
    "Письмо Verify — test_register_and_verify_email_e2e. "
    "Постусловие: delete_authenticated_user_via_api. Email: MAIL_EMAIL + tag."
)
def test_register_form_desktop(page: Page, api_manager: ApiManager):
    """Регистрация: форма, согласия, переход на interview (desktop)."""
    _started_at, _tag, email, password, username = new_plus_tagged_email()

    register_page = RegisterPage(page)
    interview_page = InterviewPage(page)

    with report_step(
        "Предусловие: открыта /auth/register, форма в начальном состоянии",
        "URL /auth/register; поля и чекбоксы видны; «Зарегистрироваться» неактивна",
    ):
        register_page.open()
        expect(page).to_have_url(re.compile(r".*/auth/register$"))

    with report_step(
        "Шаги 2–5: заполнить поля",
        "Поля username, email, пароль заполнены; «Зарегистрироваться» неактивна",
    ):
        register_page.username.fill(username)
        register_page.email.fill(email)
        register_page.password.fill(password)
        register_page.password_confirmation.fill(password)
        register_page.expect_submit_disabled()

    with report_step(
        "Шаг 6: согласие на обработку ПД",
        "Чекбокс ПД отмечен; «Зарегистрироваться» неактивна",
    ):
        register_page.check_privacy_consent()

    with report_step(
        "Шаг 7: согласие с договором-офертой",
        "Чекбокс оферты отмечен; «Зарегистрироваться» активна",
    ):
        register_page.check_offer_consent()

    with report_step(
        "Шаг 8: опциональное согласие на рассылку",
        "Чекбокс рассылки отмечен; «Зарегистрироваться» активна",
    ):
        register_page.check_marketing_consent()

    with report_step(
        "Шаг 9: «Зарегистрироваться»",
        "URL /interview; модалка Onboarding 1/5 видна (онбординг не проходим)",
    ):
        register_page.submit_registration()
        register_page.wait_after_successful_register()
        interview_page.expect_on_interview_route()
        interview_page.onboarding.expect_onboarding_visible()

    with report_step(
        "Постусловие: удалить пользователя через API",
        "login → DELETE /users/:id → login 401",
    ):
        delete_authenticated_user_via_api(api_manager, email, password)
