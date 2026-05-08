import os
import random
import re
import string
import time
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import allure
import pytest
import requests

from api.api_manager import ApiManager
from mail.mail_client import MailClient
from resources.mail_creds import MailCreds
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

_EMAIL_RATE_LIMIT_RE = re.compile(
    r"restricted in a period of\s+(?P<seconds>[\d.]+)\s+seconds", re.I
)


@allure.epic("Тест - Верификация email по письму")
@allure.title("E2E: регистрация → письмо (IMAP) → verify-email → isVerified=true")
def test_email_verification_e2e(api_manager: ApiManager):
    assert MailCreds.EMAIL and MailCreds.PASSWORD and MailCreds.HOST, (
        "Mail creds are not configured. Set MAIL_HOST/MAIL_EMAIL/MAIL_PASSWORD."
    )

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
            "avatarUrl": DataGenerator.random_avatar_url(),
        }

    with allure.step("Регистрируем пользователя (с ретраями на 503)"):
        started_at = datetime.now(timezone.utc)
        last_signup = None
        for attempt in range(5):
            last_signup = api_manager.auth_api.register_user(
                user_payload, expected_status=[201, 503, 409]
            )
            if last_signup.status_code == 201:
                break
            if last_signup.status_code == 409:
                # email/phone could conflict in shared env; re-generate phone and try again
                user_payload["phone"] = DataGenerator.random_phone()
            time.sleep(2 * (attempt + 1))

        assert last_signup is not None
        if last_signup.status_code == 409:
            pytest.fail("Registration conflict after retries. Try a new tag/phone.")
        assert last_signup.status_code == 201, "signUp is unavailable (503) after retries"

        user_id = last_signup.json().get("user", {}).get("id")
        assert user_id, "user.id is missing after signUp"

    with allure.step("Логинимся и триггерим отправку verification email"):
        api_manager.auth_api.authenticate((recipient_email, password))
        deadline = time.time() + 180
        last_send = None
        while time.time() < deadline:
            last_send = api_manager.auth_api.send_verification_email(
                {"id": user_id}, expected_status=[200, 403]
            )
            if last_send.status_code == 200:
                payload = {}
                try:
                    payload = last_send.json()
                except Exception:
                    payload = {}
                assert "sent" in str(payload.get("message", last_send.text)).lower()
                break

            # 403: rate limit — wait suggested period and retry
            wait_s = 60.0
            try:
                err = last_send.json()
                description = str(err.get("description", ""))
                match = _EMAIL_RATE_LIMIT_RE.search(description)
                if match:
                    wait_s = float(match.group("seconds"))
            except Exception:
                pass

            # Add a small buffer to avoid retrying too early
            time.sleep(min(wait_s + 1.0, 65.0))

        assert last_send is not None
        assert last_send.status_code == 200, (
            "Verification email could not be sent due to rate limiting."
        )

    with allure.step("Ждём письмо в IMAP и извлекаем ссылку verify-email"):
        client = MailClient(
            host=MailCreds.HOST,
            email=MailCreds.EMAIL,
            password=MailCreds.PASSWORD,
            folder=MailCreds.FOLDER,
            port=MailCreds.PORT,
        )
        message = client.wait_for_message(
            subject="Verify Your Email",
            to_contains=recipient_email,
            since=started_at,
            timeout_s=180,
            poll_interval_s=3,
        )
        verification_url = client.get_message_link(message)

    with allure.step("Удаляем письмо из ящика, чтобы не мешало следующим прогонам"):
        client.delete_message(message.uid)

    with allure.step("Парсим token из ссылки и подтверждаем email через API"):
        parsed = urlparse(verification_url)
        token = (parse_qs(parsed.query).get("token") or [None])[0]
        assert token, "verification token is missing in link"

        verify_resp = requests.get(
            "https://api.yeatwork.ru/auth/verify-email",
            params={"token": token},
            timeout=15,
        )
        assert verify_resp.status_code in {200, 302}

    with allure.step("Проверяем, что пользователь стал isVerified=true"):
        api_manager.auth_api.authenticate((recipient_email, password))
        profile = api_manager.auth_api.profile().json()
        assert profile.get("isVerified") is True, (
            "User email is not verified after verification link click"
        )
