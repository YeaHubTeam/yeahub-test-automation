"""Подтверждение Email зарегистрированного пользователя (desktop), Test IT [422].

https://team-vz1y.testit.software/browse/422

Предусловия: API signUp (неподтверждённый) + UI login → /interview + IMAP-ящик.
Шаги 1–6 по ручному ТК. Teardown: fixture `unverified_mail_registered_user`.
"""

import os
from datetime import datetime, timezone
from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from api.api_manager import ApiManager
from pages.auth.login_page import LoginPage
from pages.interview.interview_page import InterviewPage
from pages.settings.email_verify_page import EmailVerifyPage
from tests.mail.verification_flow import (
    assert_profile_not_verified,
    assert_profile_verified,
    wait_imap_verification_link_or_resend,
)
from tests.ui.flows.email_verify_flow import open_verification_link_in_new_tab
from tests.ui.flows.register_mail_interview_flow import require_mail_creds
from utils.reporting import report_step


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Email verification")
@allure.title("Подтверждение Email зарегистрированного пользователя (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "auth")
@testit.workItemIds("da8e428d-144b-46d5-8629-627dd27a97bd")
@testit.externalId("yeahub-ui-auth-email-verify-desktop-422")
@testit.title("Подтверждение Email зарегистрированного пользователя (desktop)")
@testit.description(
    "Ручной ТК 422: signUp + UI login → interview → онбординг 1/5–5/5 (техн.). "
    "Шаг 1: CTA «Подтвердить e-mail» в шапке или /settings#email-verify. "
    "IMAP → подтверждение → «Почта успешно подтверждена». Teardown: delete user."
)
@pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
)
def test_email_verify_registered_user_desktop(
    page: Page,
    api_manager: ApiManager,
    unverified_mail_registered_user: dict[str, Any],
):
    """Подтверждение Email на /interview и в настройках (desktop)."""
    require_mail_creds()

    email = unverified_mail_registered_user["email"]
    password = unverified_mail_registered_user["password"]
    username = unverified_mail_registered_user["username"]
    user_id = unverified_mail_registered_user["id"]
    mail_since = unverified_mail_registered_user.get("mail_since") or datetime.now(timezone.utc)

    login_page = LoginPage(page)
    interview_page = InterviewPage(page)
    email_verify_page = EmailVerifyPage(page)

    with report_step(
        "Предусловие 1: пользователь зарегистрирован на платформе через Email",
        "У пользователя есть доступ к аккаунту по email и паролю (API signUp 201)",
    ):
        pass

    with report_step(
        "Предусловие 2: email пользователя не подтверждён",
        "isVerified=false в профиле (проверено в fixture и повторно перед UI)",
    ):
        assert_profile_not_verified(api_manager, email, password)

    with report_step(
        "Предусловие 3: пользователь авторизован на странице /interview",
        "Открыта страница «Тренажёр собеседований» (имя в шапке, не /auth/login)",
    ):
        login_page.open()
        login_page.fill_credentials(email, password)
        login_page.submit()
        interview_page.expect_authorized_after_login(username=username)

    with report_step(
        "Предусловие 4: доступ к почтовому ящику, указанному при регистрации",
        "MAIL_HOST/MAIL_EMAIL/MAIL_PASSWORD заданы (require_mail_creds)",
    ):
        pass

    with report_step(
        "Шаг 1: перейти на верификацию email (CTA в шапке interview или /settings#email-verify)",
        "Раздел «Верификация», «Подтвердите ваш e-mail», поле email; при автоотправке — тост о письме",
    ):
        email_verify_page.open_step1_from_interview(interview_page)
        email_verify_page.expect_after_first_open(email=email)

    with report_step(
        "Шаг 2: обновить страницу",
        "Заголовок «Подтвердите ваш e-mail», поле email, кнопка «Подтвердить»; "
        "уведомление «Письмо успешно отправлено на почту» не отображается",
    ):
        email_verify_page.reload_page()
        email_verify_page.expect_form_after_reload(email=email)

    with report_step(
        "Шаг 3: нажать «Подтвердить» справа от поля email",
        "Клик по кнопке; при успехе — тост; при ошибке/rate limit после signUp — письмо ищем в IMAP",
    ):
        ui_sent_ok = email_verify_page.click_confirm_send_email()
        if ui_sent_ok:
            email_verify_page.expect_after_resend_click()

    with report_step(
        "Шаг 4: открыть в ящике письмо YeaHub с темой Verify Your Email",
        "Письмо от signUp/шага 3 или повторная отправка через API при отсутствии в IMAP",
    ):
        verification_url = wait_imap_verification_link_or_resend(
            api_manager,
            user_id=user_id,
            recipient_email=email,
            since=mail_since,
            imap_first_timeout_s=90.0,
            imap_after_resend_timeout_s=180.0,
        )

    with report_step(
        "Шаг 5: нажать в письме «Подтвердить Email»",
        "Новая вкладка: «Email verified successfully!» и редирект на app.yeatwork.ru",
    ):
        open_verification_link_in_new_tab(page, verification_url)

    with report_step(
        "Шаг 6: открыть /settings#email-verify",
        "Отображается надпись «Почта успешно подтверждена»",
    ):
        email_verify_page.open_email_verify_direct()
        email_verify_page.expect_email_verified_state()
        assert_profile_verified(api_manager, email, password)
