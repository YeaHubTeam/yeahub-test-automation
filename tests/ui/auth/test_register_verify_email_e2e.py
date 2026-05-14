import os
import re
import time

import allure
import pytest
import testit
from playwright.sync_api import Page, expect

from api.api_manager import ApiManager
from pages.auth.register_page import RegisterPage
from pages.settings.settings_page import SettingsPage
from tests.mail.verification_flow import (
    build_signup_payload_for_api,
    delete_authenticated_user_via_api,
    same_email_signup_api_probe_enabled,
    wait_same_email_signup_ready_via_api_probe,
)
from tests.ui.flows.register_mail_interview_flow import (
    new_plus_tagged_email,
    register_ui_through_interview_first_continue,
    require_mail_creds,
    verify_email_via_imap_after_first_onboarding_continue,
)
from tests.ui.flows.same_email_retry_config import (
    same_email_retry_max_wait_seconds,
    same_email_retry_poll_interval_seconds,
)
from utils.data_generator import DataGenerator


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
        require_mail_creds()

    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()

    with allure.step("Register new user via UI"):
        interview_page = register_ui_through_interview_first_continue(
            page,
            username,
            recipient_email,
            password,
        )

    with allure.step("API + IMAP: verify email (см. register_mail_interview_flow)"):
        verify_email_via_imap_after_first_onboarding_continue(
            api_manager,
            recipient_email=recipient_email,
            password=password,
            started_at=started_at,
        )

    # Повторная регистрация на тот же email: дефолты 120 с / poll 4 с / API probe — tests/ui/flows/same_email_retry_config.py
    # Быстрый путь (только тост): REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS=0
    same_email_retry_max_s = same_email_retry_max_wait_seconds()
    same_email_poll_s = same_email_retry_poll_interval_seconds()

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
