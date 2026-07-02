"""E2E API: верификация email, Test IT [466](https://team-vz1y.testit.software/browse/466).

signUp → send verification email → IMAP → GET verify-email → profile isVerified=true.
"""

import os
import random
import string
from datetime import datetime, timezone

import allure
import pytest
import testit

from api.api_manager import ApiManager
from resources.mail_creds import MailCreds
from tests.mail.signup_retry import authenticate_with_retries, register_user_with_retries
from tests.mail.verification_flow import (
    confirm_email_via_link,
    delete_authenticated_user_via_api,
    wait_imap_verification_link_or_resend,
)
from tests.ui.flows.register_mail_interview_flow import require_mail_creds
from utils.data_generator import DataGenerator

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.regression,
    pytest.mark.skipif(
        os.getenv("RUN_MAIL_INTEGRATION") != "1",
        reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
    ),
]


@allure.epic("Тест - Верификация email по письму")
@allure.title("E2E: регистрация → письмо (IMAP) → verify-email → isVerified=true")
@testit.workItemIds("d8198169-d467-4cce-acca-9b7769ff948c")
@testit.externalId("yeahub-api-auth-email-verification-e2e-466")
@testit.title("E2E API: верификация email (signUp → письмо → verify-email → isVerified=true)")
def test_email_verification_e2e(api_manager: ApiManager):
    """E2E API: верификация email (signUp → письмо → verify-email → isVerified=true)."""
    require_mail_creds()

    recipient_email: str | None = None
    password: str | None = None
    try:
        with allure.step("Готовим уникальный +tag email и тестовые данные пользователя"):
            inbox_email = MailCreds.EMAIL
            local, domain = inbox_email.split("@", 1)
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
            tag = f"e2e-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{suffix}"
            recipient_email = f"{local}+{tag}@{domain}"

            password = DataGenerator.random_password()
            user_payload = {
                "username": f"verify_{tag}",
                "password": password,
                "email": recipient_email,
                "phone": DataGenerator.random_phone(),
                "country": DataGenerator.random_country(),
                "city": DataGenerator.random_city(),
                "birthday": DataGenerator.random_birthday(),
                "address": DataGenerator.random_address(),
                "avatarUrl": None,
            }

        with allure.step("Регистрируем пользователя (с ретраями на 503)"):
            started_at = datetime.now(timezone.utc)

            def _on_signup_retry(_attempt: int, response) -> None:
                if response.status_code == 409:
                    user_payload["phone"] = DataGenerator.random_phone()

            last_signup = register_user_with_retries(
                api_manager, user_payload, on_retry=_on_signup_retry
            )
            if last_signup.status_code == 409:
                pytest.fail("Registration conflict after retries. Try a new tag/phone.")
            assert last_signup.status_code == 201, "signUp is unavailable (503) after retries"

            user_id = last_signup.json().get("user", {}).get("id")
            assert user_id, "user.id is missing after signUp"

        with allure.step(
            "Логинимся и ждём письмо verify-email (IMAP сначала, send API при необходимости)"
        ):
            authenticate_with_retries(api_manager, recipient_email, password)
            verification_url = wait_imap_verification_link_or_resend(
                api_manager,
                user_id=user_id,
                recipient_email=recipient_email,
                since=started_at,
            )

        with allure.step("Парсим token из ссылки и подтверждаем email через API"):
            confirm_email_via_link(verification_url)

        with allure.step("Проверяем, что пользователь стал isVerified=true"):
            authenticate_with_retries(api_manager, recipient_email, password)
            profile = api_manager.auth_api.profile().json()
            assert profile.get("isVerified") is True, (
                "User email is not verified after verification link click"
            )
    finally:
        if recipient_email and password:
            with allure.step("Teardown: удалить тестового пользователя через API"):
                delete_authenticated_user_via_api(api_manager, recipient_email, password)
