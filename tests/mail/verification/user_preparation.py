"""Высокоуровневая подготовка тестового пользователя: payload для signUp + верификация email."""

import logging
import os
from datetime import datetime

from api.api_manager import ApiManager
from mail.exceptions import MessageNotFoundError
from tests.mail.verification.actions import confirm_email_via_link, send_verification_email_with_retries
from tests.mail.verification.asserts import assert_profile_not_verified, assert_profile_verified
from tests.mail.verification.polling import wait_imap_verification_link

logger = logging.getLogger(__name__)


def build_signup_payload_for_api(username: str, email: str, password: str) -> dict:
    """Тело POST /auth/signUp в том же виде, что и `test_user` в conftest."""
    from utils.data_generator import DataGenerator

    return {
        "username": username,
        "password": password,
        "email": email,
        "phone": DataGenerator.random_phone(),
        "country": DataGenerator.random_country(),
        "city": DataGenerator.random_city(),
        "birthday": DataGenerator.random_birthday(),
        "address": DataGenerator.random_address(),
        "avatarUrl": str(DataGenerator.random_avatar_url()),
    }


def verify_api_registered_user_email(
        api_manager: ApiManager,
        *,
        email: str,
        password: str,
        user_id: str,
        started_at: datetime,
        imap_first_timeout_s: float = 20.0,
        imap_after_resend_timeout_s: float = 120.0,
) -> None:
    """После POST /auth/signUp: IMAP (письмо могло уйти на signUp) → иначе send → IMAP → confirm."""
    assert_profile_not_verified(api_manager, email, password)
    logger.info(
        "IMAP first (%.0fs): check if signUp already sent verification email to %s",
        imap_first_timeout_s,
        email,
    )
    try:
        verification_url = wait_imap_verification_link(
            recipient_email=email,
            since=started_at,
            timeout_s=imap_first_timeout_s,
        )
        logger.info("Verification email found in IMAP without send-verification-email API")
    except MessageNotFoundError:
        logger.info(
            "No email in IMAP after %.0fs — send-verification-email for %s (user_id=%s)",
            imap_first_timeout_s,
            email,
            user_id,
        )
        send_verification_email_with_retries(api_manager, user_id)
        logger.info(
            "Waiting for Verify Your Email in IMAP for %s (timeout %.0fs)...",
            email,
            imap_after_resend_timeout_s,
        )
        verification_url = wait_imap_verification_link(
            recipient_email=email,
            since=started_at,
            timeout_s=imap_after_resend_timeout_s,
        )
    confirm_email_via_link(verification_url)
    assert_profile_verified(api_manager, email, password)


def same_email_signup_api_probe_enabled() -> bool:
    """REGISTER_SAME_EMAIL_API_PROBE=0 — старое поведение (глухой sleep без API-проверки)."""
    raw = os.getenv("REGISTER_SAME_EMAIL_API_PROBE", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")