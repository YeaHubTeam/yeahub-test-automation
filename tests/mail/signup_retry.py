"""YH-2137: shared retry policy for live integration (signUp, login, payment API)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

from api.api_manager import ApiManager
from utils.retry import SIGNUP_MAX_ATTEMPTS, request_with_retries


def register_user_with_retries(
    api_manager: ApiManager,
    user_payload: dict[str, Any],
    *,
    on_retry: Callable[[int, requests.Response], None] | None = None,
) -> requests.Response:
    """HTTP call with backoff on transient 503 and network errors.
    Caller must assert success_status."""
    return request_with_retries(
        lambda: api_manager.auth_api.register_user(user_payload, expected_status=[201, 503]),
        success_status=201,
        max_attempts=SIGNUP_MAX_ATTEMPTS,
        on_retry=on_retry,
    )


def login_user_with_retries(
    api_manager: ApiManager,
    login_data: dict[str, Any],
) -> "requests.Response":
    return request_with_retries(
        lambda: api_manager.auth_api.login_user(login_data, expected_status=[201, 503]),
        success_status=201,
    )


def authenticate_with_retries(api_manager: ApiManager, email: str, password: str) -> None:
    api_manager.auth_api.session.cookies.clear()
    last_response = login_user_with_retries(api_manager, {"username": email, "password": password})
    assert last_response.status_code == 201, "login is unavailable (503) after retries"
    payload = last_response.json()
    token = payload.get("accessToken") or payload.get("access_token")
    if not token:
        raise KeyError(f"Token is missing in login response. Keys found: {list(payload.keys())}")
    api_manager.auth_api._update_session_headers(Authorization=f"Bearer {token}")


def password_change_with_retries(
    api_manager: ApiManager,
    user_id,
    payload: dict[str, Any],
    *,
    success_status: int = 200,
) -> requests.Response:
    """password-change with backoff on 503 and transient network errors."""
    return request_with_retries(
        lambda: api_manager.auth_api.password_change(
            user_id, payload, expected_status=[success_status, 503]
        ),
        success_status=success_status,
    )
