import os
import random
import re
import string
import time
from datetime import datetime, timezone

import allure
import pytest
import testit
from playwright.sync_api import Page, expect

from api.api_manager import ApiManager
from pages.auth.register_page import RegisterPage
from pages.interview.interview_page import InterviewPage
from pages.settings.settings_page import SettingsPage
from resources.mail_creds import MailCreds
from tests.mail.verification_flow import (
    assert_profile_not_verified,
    assert_profile_verified,
    build_signup_payload_for_api,
    confirm_email_via_link,
    delete_authenticated_user_via_api,
    profile_user_id,
    same_email_signup_api_probe_enabled,
    wait_imap_verification_link_or_resend,
    wait_same_email_signup_ready_via_api_probe,
)
from utils.data_generator import DataGenerator


def _int_env(name: str, default: int = 0) -> int:
    raw = os.getenv(name, str(default) if default else "").strip()
    if raw == "":
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def _same_email_retry_max_wait_s() -> int:
    """Общий бюджет времени; явный MAX_WAIT или legacy REGISTER_SAME_EMAIL_RETRY_AFTER_SECONDS."""
    if os.getenv("REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS", "").strip() != "":
        return _int_env("REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS", 0)
    return _int_env("REGISTER_SAME_EMAIL_RETRY_AFTER_SECONDS", 0)


def _same_email_retry_poll_interval_s() -> float:
    raw = os.getenv("REGISTER_SAME_EMAIL_RETRY_POLL_INTERVAL_SECONDS", "4").strip()
    try:
        v = float(raw.replace(",", "."))
    except ValueError:
        v = 4.0
    return min(5.0, max(3.0, v))


def _wait_same_email_cooldown(page: Page, total_s: int, poll_s: float) -> None:
    """Ждём limited_period без повторных submit: нарезка sleep на poll_s (один submit — только после паузы).

    Повторные «Зарегистрироваться» давали гонку: бэкенд уже создал пользователя, UI остался на /auth/register,
    следующий submit — «Пользователь уже существует».
    """
    if total_s <= 0:
        return
    deadline = time.monotonic() + float(total_s)
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        page.wait_for_timeout(int(min(poll_s, remaining) * 1000))


@pytest.mark.ui
@pytest.mark.smoke
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Register")
@allure.title("Register page opens")
@allure.severity(allure.severity_level.MINOR)
@allure.label("component", "auth")
def test_register_page_opens(page: Page):
    with allure.step("Open /auth/register"):
        register_page = RegisterPage(page)
        register_page.open()
        expect(page).to_have_url(re.compile(r".*/auth/register$"))


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Register + email verification")
@allure.title("Register → IMAP verify → onboarding → delete → optional same-email re-register")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "auth")
@testit.workItemIds("c012998a-c5a3-4985-921f-73ad28595b8b")
# Must match TMS autotest "External ID" (library); human-readable ids require a matching TMS row or auto-create.
@testit.externalId("b825e5e369cae96f5ffbc8333e3f132c05d998cb2cae6eef1b8c61cb82d7deae")
@testit.title("Register and verify email (E2E)")
@pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
)
def test_register_and_verify_email_e2e(page: Page, api_manager: ApiManager):
    with allure.step("Preconditions: mail creds configured"):
        assert MailCreds.EMAIL and MailCreds.PASSWORD and MailCreds.HOST, (
            "Mail creds are not configured. Set MAIL_HOST/MAIL_EMAIL/MAIL_PASSWORD."
        )

    started_at = datetime.now(timezone.utc)
    inbox_email = MailCreds.EMAIL
    local, domain = inbox_email.split("@", 1)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    tag = f"e2e-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{suffix}"
    recipient_email = f"{local}+{tag}@{domain}"

    password = DataGenerator.random_password()
    username = DataGenerator.random_username()

    with allure.step("Register new user via UI"):
        register_page = RegisterPage(page)
        register_page.open()
        expect(page).to_have_url(re.compile(r".*/auth/register$"))

        register_page.fill_register_form(username, recipient_email, password)
        register_page.check_checkboxes()
        register_page.submit_registration()
        register_page.wait_after_successful_register()

    interview_page = InterviewPage(page)
    with allure.step("Onboarding: open and continue first step"):
        interview_page.onboarding.expect_onboarding_visible()
        interview_page.onboarding.click_continue()

    # API: тот же email/password — authenticate() сам кладёт Bearer в session requests (без токена из браузера).
    with allure.step("API: verify profile is NOT verified yet"):
        assert_profile_not_verified(api_manager, recipient_email, password)

    with allure.step("IMAP: fetch verification email (or resend)"):
        profile = api_manager.auth_api.profile().json()
        user_id = profile_user_id(profile)
        verification_url = wait_imap_verification_link_or_resend(
            api_manager,
            user_id=user_id,
            recipient_email=recipient_email,
            since=started_at,
        )

    with allure.step("Confirm email via verification link"):
        confirm_email_via_link(verification_url)
        assert_profile_verified(api_manager, recipient_email, password)

    # Постусловие ТК: настройки → аккаунт → удаление → редирект на регистрацию.
    # Повторная регистрация с тем же email: по умолчанию бэкенд сразу отвечает limited_period
    # (см. tests/api/test_send_verification_email.py) — проверяем тост.
    # Повторный signup: REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS (или legacy *_AFTER_SECONDS) —
    # только ожидание нарезкой REGISTER_SAME_EMAIL_RETRY_POLL_INTERVAL_SECONDS, затем один submit (без цикла submit).
    # После успеха — delete_authenticated_user_via_api.
    same_email_retry_max_s = _same_email_retry_max_wait_s()
    same_email_poll_s = _same_email_retry_poll_interval_s()

    with allure.step("Complete onboarding and delete account via UI"):
        interview_page.onboarding.complete_onboarding_through_close()
        settings = SettingsPage(page)
        settings.open_account_direct()
        settings.delete_current_account(username)

    register_page = RegisterPage(page)
    with allure.step("Open register page with clean browser session"):
        register_page.open_with_clean_session()
        expect(page).to_have_url(re.compile(r".*/auth/register$"))
    password2 = DataGenerator.random_password()
    username2 = DataGenerator.random_username()
    register_page.fill_register_form(username2, recipient_email, password2)
    register_page.check_checkboxes()
    if same_email_retry_max_s > 0:
        deadline = time.monotonic() + float(same_email_retry_max_s)
        if same_email_signup_api_probe_enabled():
            signup_payload = build_signup_payload_for_api(username2, recipient_email, password2)
            with allure.step(
                "Same email re-register: wait until backend cooldown passes (API probe)"
            ):
                token = wait_same_email_signup_ready_via_api_probe(
                    api_manager,
                    signup_payload,
                    deadline_monotonic=deadline,
                    poll_s=same_email_poll_s,
                )
            with allure.step("Same email re-register: enter /interview without double-submit"):
                if token:
                    register_page.finish_registration_after_api_signup(token)
                else:
                    register_page.submit_registration()
        else:
            with allure.step("Same email re-register: blind wait then one submit (no submit loop)"):
                _wait_same_email_cooldown(page, same_email_retry_max_s, same_email_poll_s)
                register_page.submit_registration()
        with allure.step("Assert register succeeded and cleanup second user via API"):
            register_page.wait_after_successful_register()
            delete_authenticated_user_via_api(api_manager, recipient_email, password2)
    else:
        with allure.step("Same email re-register: expect cooldown toast (fast path)"):
            register_page.submit_registration()
            expect(page).to_have_url(re.compile(r".*/auth/register"))
            register_page.expect_email_reuse_cooldown_toast()
