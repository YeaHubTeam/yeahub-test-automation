"""Одноразовые действия с ретраями на транзиентные ошибки (rate limit, 502/503/504)."""

import re
import time
from urllib.parse import parse_qs, urlparse

import requests

from api.api_manager import ApiManager
from constants.constants import BASE_URL
from utils.retry import INTEGRATION_MAX_ATTEMPTS, default_backoff

_VERIFY_EMAIL_SUCCESS = {200, 302}
_VERIFY_EMAIL_TIMEOUT = (15, 30)
_TRANSIENT_VERIFY_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ReadTimeout,
)
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


def confirm_email_via_link(verification_url: str) -> None:
    """Переход по ссылке подтверждения email, с ретраями на 503/сетевые ошибки."""
    parsed = urlparse(verification_url)
    token = (parse_qs(parsed.query).get("token") or [None])[0]
    assert token, "verification token is missing in link"
    base = BASE_URL.rstrip("/")
    verify_url = f"{base}/auth/verify-email"
    last_response: requests.Response | None = None
    for attempt in range(INTEGRATION_MAX_ATTEMPTS):
        try:
            last_response = requests.get(
                verify_url,
                params={"token": token},
                timeout=_VERIFY_EMAIL_TIMEOUT,
            )
        except _TRANSIENT_VERIFY_ERRORS as exc:
            if attempt == INTEGRATION_MAX_ATTEMPTS - 1:
                raise exc
            time.sleep(default_backoff(attempt))
            continue
        if last_response.status_code in _VERIFY_EMAIL_SUCCESS:
            return
        if last_response.status_code == 503:
            time.sleep(default_backoff(attempt))
            continue
        assert last_response.status_code in _VERIFY_EMAIL_SUCCESS
    assert last_response is not None
    assert last_response.status_code in _VERIFY_EMAIL_SUCCESS