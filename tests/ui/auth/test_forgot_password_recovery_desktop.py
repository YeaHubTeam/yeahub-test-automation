"""Восстановление пароля через forgot-password + письмо (desktop), Test IT [115].

https://team-vz1y.testit.software/browse/115

Flow: forgot-password → IMAP Reset Password → recovery → interview; login с новым паролем.
Setup: API signUp + IMAP verify (`verified_registered_user`). UI без сессии.
Teardown: delete_user с новым паролем. Шаг 10: API logout + UI login (не UI logout).
"""

import os
from datetime import datetime, timezone
from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from api.api_manager import ApiManager
from pages.auth.forgot_password_page import ForgotPasswordPage
from pages.auth.login_page import LoginPage
from pages.auth.password_recovery_page import PasswordRecoveryPage
from pages.interview.interview_page import InterviewPage
from pages.interview.onboarding_modal import OnboardingModal
from resources.mail_creds import MailCreds
from tests.mail.reset_password_flow import wait_imap_reset_password_link_after_ui_send
from tests.ui.flows.register_mail_interview_flow import require_mail_creds
from utils.data_generator import DataGenerator


def _require_mail_integration() -> None:
    assert MailCreds.EMAIL and MailCreds.PASSWORD and MailCreds.HOST, (
        "Mail creds are not configured. Set MAIL_HOST/MAIL_EMAIL/MAIL_PASSWORD."
    )


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Forgot password recovery")
@allure.title("Восстановление пароля через письмо (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "auth")
@testit.workItemIds("bb5e0378-6e19-44de-89b5-90bd62dec207")
@testit.externalId("yeahub-ui-auth-forgot-password-recovery-desktop-115")
@testit.title("Восстановление пароля через письмо (desktop)")
@pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
)
def test_forgot_password_recovery_desktop(
    page: Page,
    api_manager: ApiManager,
    verified_registered_user: dict[str, Any],
):
    """Восстановление пароля через письмо (desktop)."""
    _require_mail_integration()
    require_mail_creds()

    email = verified_registered_user["email"]
    username = verified_registered_user["username"]
    new_password = DataGenerator.random_password()

    login_page = LoginPage(page)
    login_page.clear_browser_session()
    forgot_page = ForgotPasswordPage(page)
    recovery_page = PasswordRecoveryPage(page)

    with allure.step("Предусловие: не авторизован, открыта страница login"):
        login_page.open_app_expect_login()
        login_page.expect_login_form_elements_visible()

    with allure.step("Шаги 1–2: login → «Забыли пароль?» → /auth/forgot-password"):
        login_page.click_forgot_password()
        forgot_page.expect_forgot_password_page()

    with allure.step("Шаги 3–4: email → «Отправить» → модалка о письме"):
        forgot_page.fill_email(email)
        forgot_page.expect_no_validation_errors()
        forgot_page.expect_submit_enabled()
        sent_after = datetime.now(timezone.utc)
        forgot_page.click_submit()
        forgot_page.expect_email_sent_modal()

    with allure.step("Шаги 5–6: IMAP Reset Password → открыть password-recovery"):
        recovery_url = wait_imap_reset_password_link_after_ui_send(
            api_manager,
            email=email,
            since=sent_after,
        )
        recovery_page.open(recovery_url)

    with allure.step("Шаги 7–8: новый пароль + повтор, «Сохранить» доступна"):
        recovery_page.fill_new_password(new_password)
        recovery_page.fill_confirm_password(new_password)
        recovery_page.expect_no_validation_errors()
        recovery_page.expect_save_enabled()

    with allure.step("Шаг 9: «Сохранить» → interview + тост «Пароль успешно изменен»"):
        recovery_page.click_save()
        recovery_page.expect_success_toast()
        recovery_page.expect_redirect_to_interview()
        onboarding = OnboardingModal(page)
        if onboarding.modal.is_visible(timeout=2_000):
            onboarding.try_dismiss_with_escape(presses=5)
        InterviewPage(page).expect_authorized_after_login(username=username)
        verified_registered_user["active_password"] = new_password

    with allure.step("Шаг 10: API logout → UI login с новым паролем → /interview"):
        api_manager.auth_api.authenticate((email, new_password))
        api_manager.auth_api.logout(expected_status=[200, 401, 503])
        login_page.clear_browser_session()
        login_page.ensure_on_login_page()
        login_page.fill_credentials(email, new_password)
        login_page.submit()
        InterviewPage(page).expect_authorized_after_login(username=username)
