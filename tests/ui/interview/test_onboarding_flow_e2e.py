"""E2E онбординга после регистрации с почтой (связь с ручным кейсом в Test IT — workItemIds)."""

import os
import re

import allure
import pytest
import testit
from playwright.sync_api import Page, expect

from api.api_manager import ApiManager
from pages.auth.login_page import LoginPage
from pages.interview.interview_page import INTERVIEW_URL_RE, InterviewPage
from pages.layout.user_menu import UserMenu
from tests.mail.verification_flow import (
    assert_profile_specialization_selected,
    delete_authenticated_user_via_api,
)
from tests.ui.flows.register_mail_interview_flow import (
    new_plus_tagged_email,
    register_ui_through_interview_first_continue,
    require_mail_creds,
    verify_email_via_imap_after_first_onboarding_continue,
)


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@allure.epic("UI")
@allure.feature("Interview")
@allure.story("Onboarding")
@allure.title("Onboarding 1/5–5/5 → постусловия → удаление (e2e)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "interview")
@testit.workItemIds("608dd8ae-b3fa-4103-a9db-2b86c3cbe5ef")
@testit.externalId(
    "yeahub-ui-onboarding-flow-tc-147"
)  # id автотеста в библиотеке TMS; не путать с номером ручного кейса
@testit.title("Onboarding full flow (E2E)")
@pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
)
def test_onboarding_full_flow_e2e(page: Page, api_manager: ApiManager):
    with allure.step("Preconditions: mail creds (как auth e2e)"):
        require_mail_creds()

    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()

    with allure.step(
        "Register via UI → interview → onboarding step 1 (как auth e2e + проверка 1/5)"
    ):
        interview = register_ui_through_interview_first_continue(
            page,
            username,
            recipient_email,
            password,
            expect_tc_step1_progress=True,
        )
        onboarding = interview.onboarding

    with allure.step("IMAP + verify (сразу после первого Continue — как auth e2e)"):
        verify_email_via_imap_after_first_onboarding_continue(
            api_manager,
            recipient_email=recipient_email,
            password=password,
            started_at=started_at,
        )

    with allure.step("После verify: шаг 2/5 и шаги модалки 2–7"):
        onboarding.expect_progress_fraction(2, 5)
        onboarding.expect_onboarding_second_step_visible()
        onboarding.complete_tc_steps_2_through_7()

    with allure.step("Post: stay on interview URL (no forced redirect off interview)"):
        expect(page).to_have_url(INTERVIEW_URL_RE)

    with allure.step("Post 1: reload — onboarding does not reappear"):
        page.reload(wait_until="domcontentloaded")
        onboarding.expect_onboarding_hidden(timeout_ms=20_000)

    with allure.step("Post 2: Profile → Interview — onboarding does not reappear"):
        interview.open_profile_via_nav_link()
        interview.open_interview_via_nav_link()
        onboarding.expect_onboarding_hidden(timeout_ms=15_000)

    with allure.step("Post 3: logout → login — no onboarding, specialization persisted (API)"):
        UserMenu(page).logout_via_profile_menu()
        login_page = LoginPage(page)
        login_page.open()
        login_page.fill_credentials(recipient_email, password)
        login_page.submit()
        expect(page).to_have_url(INTERVIEW_URL_RE, timeout=30_000)
        onboarding.expect_onboarding_hidden(timeout_ms=20_000)
        assert_profile_specialization_selected(api_manager, recipient_email, password)

    with allure.step("Post 4: delete user via API (сценарий допускает teardown через API)"):
        delete_authenticated_user_via_api(api_manager, recipient_email, password)
