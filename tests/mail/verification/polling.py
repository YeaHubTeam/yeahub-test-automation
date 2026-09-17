"""Функции ожидания: цикл + sleep до наступления условия.

Три разных условия, за которыми ждём:
- письмо с подтверждением дошло в IMAP;
- профиль стал verified (eventual consistency после verify во второй вкладке);
- email освободился после гонки регистрации с тем же адресом.
"""

import json
import time
from datetime import datetime

from mail.exceptions import MessageNotFoundError
from mail.mail_client import MailClient
from resources.mail_creds import MailCreds

from api.api_manager import ApiManager
from tests.mail.signup_retry import authenticate_with_retries
from tests.mail.verification.actions import send_verification_email_with_retries
from tests.mail.verification.asserts import assert_profile_verified, profile_is_verified
from tests.mail.verification.session_context import anonymous_session


def wait_imap_verification_link(
        *,
        recipient_email: str,
        since: datetime,
        min_date: datetime | None = None,
        timeout_s: float = 180.0,
        poll_interval_s: float = 3.0,
        settle_s: float = 5.0,
) -> str:
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
        since=since,
        min_date=min_date,
        timeout_s=timeout_s,
        poll_interval_s=poll_interval_s,
    )
    if settle_s > 0:
        time.sleep(settle_s)
        try:
            message = client.find_message(
                subject="Verify Your Email",
                to_contains=recipient_email,
                since=since,
                min_date=min_date,
            )
        except MessageNotFoundError:
            pass
    link = client.get_message_link(message)
    client.delete_message(message.uid)
    return link


def wait_imap_verification_link_or_resend(
        api_manager: ApiManager,
        *,
        user_id: str,
        recipient_email: str,
        since: datetime,
        min_date: datetime | None = None,
        imap_first_timeout_s: float = 90.0,
        imap_after_resend_timeout_s: float = 180.0,
        poll_interval_s: float = 3.0,
        settle_s: float = 5.0,
) -> str:
    """Сначала ждём письмо; если не пришло за imap_first_timeout_s — резенд и снова ждём."""
    try:
        return wait_imap_verification_link(
            recipient_email=recipient_email,
            since=since,
            min_date=min_date,
            timeout_s=imap_first_timeout_s,
            poll_interval_s=poll_interval_s,
            settle_s=settle_s,
        )
    except MessageNotFoundError:
        send_verification_email_with_retries(api_manager, user_id)
        return wait_imap_verification_link(
            recipient_email=recipient_email,
            since=since,
            min_date=min_date,
            timeout_s=imap_after_resend_timeout_s,
            poll_interval_s=poll_interval_s,
            settle_s=settle_s,
        )


def wait_until_profile_verified(
        api_manager: ApiManager,
        email: str,
        password: str,
        *,
        timeout_s: float = 60.0,
        poll_s: float = 2.0,
) -> None:
    """Ждём isVerified=true после verify во второй вкладке (SPA/API eventual consistency)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        authenticate_with_retries(api_manager, email, password)
        profile = api_manager.auth_api.profile().json()
        if profile_is_verified(profile):
            return
        time.sleep(poll_s)
    assert_profile_verified(api_manager, email, password)


def _response_indicates_user_email_limited_period(resp) -> bool:
    if resp.status_code not in (400, 403, 422):
        return False
    try:
        data = resp.json()
        blob = json.dumps(data, ensure_ascii=False).lower()
        msg = str(data.get("message", "")).lower()
    except Exception:
        blob = (resp.text or "").lower()
        msg = blob
    return "limited_period" in blob or "user.user.email.limited_period" in msg


def _access_token_from_auth_json(data: dict) -> str | None:
    if not data:
        return None
    token = data.get("access_token") or data.get("accessToken")
    return str(token) if token else None


def _try_login_access_token_for_signup_payload(
        api_manager: ApiManager, signup_payload: dict
) -> str | None:
    """После 409 conflict: возможно пользователь с этим email/password уже есть — логин анонимно."""
    email = signup_payload.get("email")
    password = signup_payload.get("password")
    if not email or not password:
        return None
    with anonymous_session(api_manager):
        login_resp = api_manager.auth_api.login_user(
            {"username": email, "password": password},
            expected_status=[201, 401, 403, 503],
        )
    if login_resp.status_code != 201:
        return None
    try:
        return _access_token_from_auth_json(login_resp.json())
    except Exception:
        return None


def wait_same_email_signup_ready_via_api_probe(
        api_manager: ApiManager,
        signup_payload: dict,
        *,
        deadline_monotonic: float,
        poll_s: float,
) -> str | None:
    """Публичный signUp без Bearer: пока `limited_period` — sleep; при 201 — выходим сразу.

    Возвращает access_token, если регистрация уже прошла через API-проверку
    (тогда UI submit не нужен). None — если к дедлайну 201 не случилось.
    """
    while time.monotonic() < deadline_monotonic:
        with anonymous_session(api_manager):
            resp = api_manager.auth_api.register_user(
                signup_payload,
                expected_status=[201, 400, 403, 409, 422, 502, 503, 504],
            )

        if resp.status_code in {502, 503, 504}:
            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(poll_s, remaining))
            continue

        if _response_indicates_user_email_limited_period(resp):
            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(poll_s, remaining))
            continue

        if resp.status_code == 201:
            try:
                data = resp.json()
            except Exception:
                data = {}
            token = _access_token_from_auth_json(data)
            assert token, "signUp returned 201 but access token is missing"
            return token

        if resp.status_code == 409:
            token = _try_login_access_token_for_signup_payload(api_manager, signup_payload)
            if token:
                return token
            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(poll_s, remaining))
            continue

        raise AssertionError(
            f"Unexpected signUp response while polling same-email cooldown: "
            f"status={resp.status_code} body={resp.text[:500]!r}",
        )

    return None