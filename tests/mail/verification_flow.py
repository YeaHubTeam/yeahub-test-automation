"""Общие шаги: отправка письма верификации (с ретраями на rate limit) и подтверждение по ссылке."""

import json
import os
import re
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests
from requests.utils import add_dict_to_cookiejar, dict_from_cookiejar

from api.api_manager import ApiManager
from constants.constants import BASE_URL
from mail.exceptions import MessageNotFoundError
from mail.mail_client import MailClient
from resources.mail_creds import MailCreds

_EMAIL_RATE_LIMIT_RE = re.compile(
    r"restricted in a period of\s+(?P<seconds>[\d.]+)\s+seconds", re.I
)


def send_verification_email_with_retries(
    api_manager: ApiManager, user_id, deadline_s: float = 180.0
):
    """Триггерит письмо; при 403 (rate limit) ждёт и повторяет (как в API e2e)."""
    deadline = time.time() + deadline_s
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
            return last_send

        wait_s = 60.0
        try:
            err = last_send.json()
            description = str(err.get("description", ""))
            match = _EMAIL_RATE_LIMIT_RE.search(description)
            if match:
                wait_s = float(match.group("seconds"))
        except Exception:
            pass
        time.sleep(min(wait_s + 1.0, 65.0))

    assert last_send is not None
    assert last_send.status_code == 200, (
        "Verification email could not be sent due to rate limiting."
    )
    return last_send


def wait_imap_verification_link(
    *,
    recipient_email: str,
    since: datetime,
    timeout_s: float = 180.0,
    poll_interval_s: float = 3.0,
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
        timeout_s=timeout_s,
        poll_interval_s=poll_interval_s,
    )
    link = client.get_message_link(message)
    client.delete_message(message.uid)
    return link


def wait_imap_verification_link_or_resend(
    api_manager: ApiManager,
    *,
    user_id: str,
    recipient_email: str,
    since: datetime,
    imap_first_timeout_s: float = 90.0,
    imap_after_resend_timeout_s: float = 180.0,
    poll_interval_s: float = 3.0,
) -> str:
    """Сначала ждём письмо из ящика (часто уже отправлено при UI sign-up).

    Если за `imap_first_timeout_s` письма нет — дергаем send-verification-email
    (с ретраями на rate limit) и снова ждём IMAP. Так реже попадаем в 403 сразу
    после регистрации, когда письмо уже ушло.
    """
    try:
        return wait_imap_verification_link(
            recipient_email=recipient_email,
            since=since,
            timeout_s=imap_first_timeout_s,
            poll_interval_s=poll_interval_s,
        )
    except MessageNotFoundError:
        send_verification_email_with_retries(api_manager, user_id)
        return wait_imap_verification_link(
            recipient_email=recipient_email,
            since=since,
            timeout_s=imap_after_resend_timeout_s,
            poll_interval_s=poll_interval_s,
        )


def confirm_email_via_link(verification_url: str) -> None:
    parsed = urlparse(verification_url)
    token = (parse_qs(parsed.query).get("token") or [None])[0]
    assert token, "verification token is missing in link"
    base = BASE_URL.rstrip("/")
    verify_resp = requests.get(
        f"{base}/auth/verify-email",
        params={"token": token},
        timeout=15,
    )
    assert verify_resp.status_code in {200, 302}


def profile_user_id(profile: dict) -> str:
    user = profile.get("user")
    if isinstance(user, dict) and user.get("id") is not None:
        return str(user["id"])
    assert profile.get("id") is not None, "user id missing in profile response"
    return str(profile["id"])


def profile_is_verified(profile: dict) -> bool:
    user = profile.get("user")
    if isinstance(user, dict) and "isVerified" in user:
        return user["isVerified"] is True
    return profile.get("isVerified") is True


def assert_profile_verified(api_manager: ApiManager, email: str, password: str) -> None:
    api_manager.auth_api.authenticate((email, password))
    profile = api_manager.auth_api.profile().json()
    assert profile_is_verified(profile), "User email is not verified after verification link"


def assert_profile_not_verified(api_manager: ApiManager, email: str, password: str) -> None:
    api_manager.auth_api.authenticate((email, password))
    profile = api_manager.auth_api.profile().json()
    assert not profile_is_verified(profile), (
        "Expected isVerified=false before opening verification link"
    )


def delete_authenticated_user_via_api(api_manager: ApiManager, email: str, password: str) -> None:
    """Teardown: удалить пользователя тем же Bearer, что и `registered_user` в conftest."""
    api_manager.auth_api.authenticate((email, password))
    profile = api_manager.auth_api.profile().json()
    user_id = profile_user_id(profile)
    api_manager.user_api.delete_user(user_id, expected_status=[200, 204, 404, 401])

    # Post-check: regardless of backend storage flakiness (404 storage.image.not_found),
    # ensure the user cannot authenticate anymore.
    saved_session, saved_api = _snapshot_authorization_headers(api_manager)
    saved_cookies = _snapshot_session_cookies(api_manager)
    _clear_authorization_headers(api_manager)
    api_manager.session.cookies.clear()
    try:
        # A deleted user should not be able to login with the same creds.
        login_resp = api_manager.auth_api.login_user(
            {"username": email, "password": password},
            expected_status=[201, 401, 403, 503],
        )
    finally:
        _restore_session_cookies(api_manager, saved_cookies)
        _apply_authorization_headers(api_manager, saved_session, saved_api)

    assert login_resp.status_code in {401, 403}, (
        f"Expected deleted user to be unable to login, got {login_resp.status_code}: "
        f"{login_resp.text[:300]!r}"
    )


def build_signup_payload_for_api(username: str, email: str, password: str) -> dict:
    """Тело POST /auth/signUp в том же виде, что и `test_user` в conftest (один вызов — один фиксированный payload для UI+API)."""
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


def _response_indicates_user_email_limited_period(resp: requests.Response) -> bool:
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


def same_email_signup_api_probe_enabled() -> bool:
    """REGISTER_SAME_EMAIL_API_PROBE=0 — только «глухой» sleep нарезкой (старое поведение)."""
    raw = os.getenv("REGISTER_SAME_EMAIL_API_PROBE", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _snapshot_authorization_headers(api_manager: ApiManager) -> tuple[str | None, str | None]:
    session_auth = api_manager.session.headers.get("Authorization")
    api_auth = api_manager.auth_api.headers.get("Authorization")
    return session_auth, api_auth


def _clear_authorization_headers(api_manager: ApiManager) -> None:
    api_manager.session.headers.pop("Authorization", None)
    api_manager.auth_api.headers.pop("Authorization", None)


def _apply_authorization_headers(
    api_manager: ApiManager,
    session_auth: str | None,
    api_auth: str | None,
) -> None:
    if session_auth:
        api_manager.session.headers["Authorization"] = session_auth
    else:
        api_manager.session.headers.pop("Authorization", None)
    if api_auth:
        api_manager.auth_api.headers["Authorization"] = api_auth
    else:
        api_manager.auth_api.headers.pop("Authorization", None)


def _snapshot_session_cookies(api_manager: ApiManager) -> dict:
    return dict_from_cookiejar(api_manager.session.cookies)


def _restore_session_cookies(api_manager: ApiManager, cookies_dict: dict) -> None:
    api_manager.session.cookies.clear()
    if cookies_dict:
        add_dict_to_cookiejar(api_manager.session.cookies, cookies_dict)


def _access_token_from_auth_json(data: dict) -> str | None:
    if not data:
        return None
    token = data.get("access_token") or data.get("accessToken")
    return str(token) if token else None


def _try_login_access_token_for_signup_payload(
    api_manager: ApiManager,
    signup_payload: dict,
) -> str | None:
    """После 409 conflict: возможно пользователь с этим email/password уже есть — логин без cookie/Bearer."""
    email = signup_payload.get("email")
    password = signup_payload.get("password")
    if not email or not password:
        return None
    saved_session, saved_api = _snapshot_authorization_headers(api_manager)
    saved_cookies = _snapshot_session_cookies(api_manager)
    _clear_authorization_headers(api_manager)
    api_manager.session.cookies.clear()
    try:
        login_resp = api_manager.auth_api.login_user(
            {"username": email, "password": password},
            expected_status=[201, 401, 403, 503],
        )
    finally:
        _restore_session_cookies(api_manager, saved_cookies)
        _apply_authorization_headers(api_manager, saved_session, saved_api)
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
    """Публичный signUp без Bearer: пока `user.user.email.limited_period` — sleep; при 201 — сразу выходим.

    Возвращает `access_token` из ответа signUp, если регистрация уже прошла через API (UI submit не нужен).
    Если к дедлайну 201 не было — `None` (один UI submit, как раньше после полного sleep).

    Не шлём повторные UI submit (гонка «уже существует»); тело запроса должно совпадать с тем, что потом отправит форма.

    Важно: с `requests.Session` остаются Cookie (например refresh_token от предыдущего юзера) — без очистки signUp
    даёт 409 conflict вместо 201. На время запроса убираем Bearer и все cookies.
    """
    while time.monotonic() < deadline_monotonic:
        saved_session, saved_api = _snapshot_authorization_headers(api_manager)
        saved_cookies = _snapshot_session_cookies(api_manager)
        _clear_authorization_headers(api_manager)
        api_manager.session.cookies.clear()
        try:
            resp = api_manager.auth_api.register_user(
                signup_payload,
                expected_status=[201, 400, 403, 409, 422, 502, 503, 504],
            )
        finally:
            _restore_session_cookies(api_manager, saved_cookies)
            _apply_authorization_headers(api_manager, saved_session, saved_api)

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
