"""Тот же путь, что `test_register_and_verify_email_e2e` до завершения онбординга: регистрация → 1-й Continue → IMAP → verify."""

import random
import re
import string
from datetime import datetime, timezone

from playwright.sync_api import Page, expect

from api.api_manager import ApiManager
from pages.auth.register_page import RegisterPage
from pages.interview.interview_page import InterviewPage
from resources.mail_creds import MailCreds
from tests.mail.verification_flow import (
    assert_profile_not_verified,
    assert_profile_verified,
    confirm_email_via_link,
    profile_user_id,
    wait_imap_verification_link_or_resend,
)
from utils.data_generator import DataGenerator


def require_mail_creds() -> None:
    assert MailCreds.EMAIL and MailCreds.PASSWORD and MailCreds.HOST, (
        "Mail creds are not configured. Set MAIL_HOST/MAIL_EMAIL/MAIL_PASSWORD."
    )


def new_plus_tagged_email() -> tuple[datetime, str, str, str, str]:
    """Как в auth e2e: started_at, tag, recipient_email, password, username."""
    started_at = datetime.now(timezone.utc)
    inbox_email = MailCreds.EMAIL
    local, domain = inbox_email.split("@", 1)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    tag = f"e2e-{started_at.strftime('%Y%m%d-%H%M%S')}-{suffix}"
    recipient_email = f"{local}+{tag}@{domain}"
    password = DataGenerator.random_password()
    username = DataGenerator.random_username()
    return started_at, tag, recipient_email, password, username


def register_ui_through_interview_first_continue(
    page: Page,
    username: str,
    recipient_email: str,
    password: str,
    *,
    expect_tc_step1_progress: bool = False,
) -> InterviewPage:
    """Регистрация на /auth/register и первый шаг онбординга (Continue).

    Порядок как в `test_register_and_verify_email_e2e`: после Continue сразу можно звать verify (без ожидания UI 2/5).
    `expect_tc_step1_progress=True` — доп. проверка «1/5» для e2e онбординга (см. test_onboarding_full_flow_e2e).
    """
    register_page = RegisterPage(page)
    register_page.open()
    expect(page).to_have_url(re.compile(r".*/auth/register$"))
    register_page.fill_register_form(username, recipient_email, password)
    register_page.check_checkboxes()
    register_page.submit_registration()
    register_page.wait_after_successful_register()

    interview_page = InterviewPage(page)
    interview_page.expect_on_interview_route()
    interview_page.onboarding.expect_onboarding_visible()
    if expect_tc_step1_progress:
        interview_page.onboarding.expect_progress_fraction(1, 5)
    interview_page.onboarding.click_continue()
    return interview_page


def verify_email_via_imap_after_first_onboarding_continue(
    api_manager: ApiManager,
    *,
    recipient_email: str,
    password: str,
    started_at: datetime,
) -> None:
    """Сразу после первого Continue — как в auth e2e (без ожидания UI шага 2)."""
    assert_profile_not_verified(api_manager, recipient_email, password)
    profile = api_manager.auth_api.profile().json()
    user_id = profile_user_id(profile)
    verification_url = wait_imap_verification_link_or_resend(
        api_manager,
        user_id=user_id,
        recipient_email=recipient_email,
        since=started_at,
    )
    confirm_email_via_link(verification_url)
    assert_profile_verified(api_manager, recipient_email, password)
