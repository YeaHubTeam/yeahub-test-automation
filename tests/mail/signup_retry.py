"""YH-2137: shared retry policy for live integration (signUp, login, payment API)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from api.api_manager import ApiManager

INTEGRATION_MAX_ATTEMPTS = 8
SIGNUP_MAX_ATTEMPTS = INTEGRATION_MAX_ATTEMPTS
LOGIN_MAX_ATTEMPTS = INTEGRATION_MAX_ATTEMPTS

_TRANSIENT_NETWORK_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


def integration_retry_sleep_seconds(attempt: int) -> float:
    return 3 * (attempt + 1)


def request_with_integration_retries(
    request_fn: Callable[[], requests.Response],
    *,
    success_status: int = 200,
    max_attempts: int = INTEGRATION_MAX_ATTEMPTS,
) -> requests.Response:
    """HTTP call with backoff on transient 503 and network errors. Caller must assert success_status."""
    last_response: requests.Response | None = None
    for attempt in range(max_attempts):
        try:
            last_response = request_fn()
        except _TRANSIENT_NETWORK_ERRORS as exc:
            if attempt == max_attempts - 1:
                raise exc
            time.sleep(integration_retry_sleep_seconds(attempt))
            continue
        if last_response.status_code == success_status:
            return last_response
        time.sleep(integration_retry_sleep_seconds(attempt))
    assert last_response is not None
    return last_response


def register_user_with_retries(
    api_manager: ApiManager,
    user_payload: dict[str, Any],
    *,
    on_retry: Callable[[int, requests.Response], None] | None = None,
) -> requests.Response:
    """signUp with backoff on 503/409 and transient network errors. Caller must assert status_code == 201."""
    last_response: requests.Response | None = None
    for attempt in range(SIGNUP_MAX_ATTEMPTS):
        try:
            last_response = api_manager.auth_api.register_user(
                user_payload, expected_status=[201, 503, 409]
            )
        except _TRANSIENT_NETWORK_ERRORS as exc:
            if attempt == SIGNUP_MAX_ATTEMPTS - 1:
                raise exc
            time.sleep(integration_retry_sleep_seconds(attempt))
            continue
        if last_response.status_code == 201:
            return last_response
        if on_retry is not None and attempt < SIGNUP_MAX_ATTEMPTS - 1:
            on_retry(attempt, last_response)
        time.sleep(integration_retry_sleep_seconds(attempt))
    assert last_response is not None
    return last_response


def login_user_with_retries(
    api_manager: ApiManager,
    login_data: dict[str, Any],
) -> requests.Response:
    """login with backoff on 503 and transient network errors. Caller must assert status_code == 201."""
    last_response: requests.Response | None = None
    for attempt in range(LOGIN_MAX_ATTEMPTS):
        try:
            last_response = api_manager.auth_api.login_user(login_data, expected_status=[201, 503])
        except _TRANSIENT_NETWORK_ERRORS as exc:
            if attempt == LOGIN_MAX_ATTEMPTS - 1:
                raise exc
            time.sleep(integration_retry_sleep_seconds(attempt))
            continue
        if last_response.status_code == 201:
            return last_response
        time.sleep(integration_retry_sleep_seconds(attempt))
    assert last_response is not None
    return last_response


def authenticate_with_retries(api_manager: ApiManager, email: str, password: str) -> None:
    """Login with integration retries and set Bearer on the session (same contract as auth_api.authenticate)."""
    last_response = login_user_with_retries(
        api_manager,
        {"username": email, "password": password},
    )
    assert last_response.status_code == 201, "login is unavailable (503) after retries"
    payload = last_response.json()
    token = payload.get("accessToken") or payload.get("access_token")
    if not token:
        raise KeyError(f"Token is missing in login response. Keys found: {list(payload.keys())}")
    api_manager.auth_api._update_session_headers(Authorization=f"Bearer {token}")
