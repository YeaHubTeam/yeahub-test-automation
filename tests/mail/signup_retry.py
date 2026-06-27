"""YH-2137: shared signUp/login retry policy for live integration (mail nightly)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from api.api_manager import ApiManager

SIGNUP_MAX_ATTEMPTS = 8
LOGIN_MAX_ATTEMPTS = 8


def integration_retry_sleep_seconds(attempt: int) -> float:
    return 3 * (attempt + 1)


def register_user_with_retries(
    api_manager: ApiManager,
    user_payload: dict[str, Any],
    *,
    on_retry: Callable[[int, requests.Response], None] | None = None,
) -> requests.Response:
    """signUp with backoff on 503/409. Caller must assert status_code == 201."""
    last_response: requests.Response | None = None
    for attempt in range(SIGNUP_MAX_ATTEMPTS):
        last_response = api_manager.auth_api.register_user(
            user_payload, expected_status=[201, 503, 409]
        )
        if last_response.status_code == 201:
            return last_response
        if on_retry is not None:
            on_retry(attempt, last_response)
        time.sleep(integration_retry_sleep_seconds(attempt))
    assert last_response is not None
    return last_response


def login_user_with_retries(
    api_manager: ApiManager,
    login_data: dict[str, Any],
) -> requests.Response:
    """login with backoff on 503. Caller must assert status_code == 201."""
    last_response: requests.Response | None = None
    for attempt in range(LOGIN_MAX_ATTEMPTS):
        last_response = api_manager.auth_api.login_user(login_data, expected_status=[201, 503])
        if last_response.status_code == 201:
            return last_response
        time.sleep(integration_retry_sleep_seconds(attempt))
    assert last_response is not None
    return last_response
