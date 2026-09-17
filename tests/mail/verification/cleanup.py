"""Teardown: логин и удаление тестового пользователя через API."""

import time
from typing import Literal

import requests

from api.api_manager import ApiManager
from tests.mail.verification.asserts import profile_user_id
from tests.mail.verification.session_context import anonymous_session
from utils.retry import LOGIN_MAX_ATTEMPTS, default_backoff

TeardownAuthResult = Literal["authenticated", "auth_failed", "transient_failed"]


def authenticate_for_teardown(
    api_manager: ApiManager,
    email: str,
    password: str,
    *,
    max_attempts: int = LOGIN_MAX_ATTEMPTS,
) -> TeardownAuthResult:
    """Login для teardown: отделяем неверный пароль от 503/сети (не путать с ValueError от authenticate)."""
    for attempt in range(max_attempts):
        try:
            resp = api_manager.auth_api.login_user(
                {"username": email, "password": password},
                expected_status=[201, 401, 403, 503],
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            if attempt == max_attempts - 1:
                raise exc
            time.sleep(default_backoff(attempt))
            continue

        if resp.status_code == 201:
            body = resp.json()
            token = body.get("accessToken") or body.get("access_token")
            if not token:
                raise KeyError(
                    f"Token is missing in teardown login. Keys found: {list(body.keys())}"
                )
            api_manager.auth_api._update_session_headers(Authorization=f"Bearer {token}")
            return "authenticated"
        if resp.status_code in (401, 403):
            return "auth_failed"
        if resp.status_code == 503:
            if attempt == max_attempts - 1:
                return "transient_failed"
            time.sleep(default_backoff(attempt))
            continue
        raise ValueError(
            f"Unexpected teardown login status {resp.status_code}: {resp.text[:300]!r}"
        )
    return "transient_failed"


def delete_authenticated_user_via_api(api_manager: ApiManager, email: str, password: str) -> None:
    """Teardown: удалить пользователя тем же Bearer, что и `registered_user` в conftest."""
    auth_result = authenticate_for_teardown(api_manager, email, password)
    if auth_result != "authenticated":
        raise RuntimeError(f"Teardown login failed before delete_user: {auth_result}")
    profile = api_manager.auth_api.profile().json()
    user_id = profile_user_id(profile)
    api_manager.user_api.delete_user(user_id, expected_status=[200, 204, 404])

    # Post-check: независимо от флаки хранилища при удалении (404 storage.image.not_found),
    # убеждаемся, что удалённый пользователь больше не может залогиниться.
    with anonymous_session(api_manager):
        login_resp = api_manager.auth_api.login_user(
            {"username": email, "password": password},
            expected_status=[201, 401, 403, 503],
        )

    assert login_resp.status_code in {401, 403}, (
        f"Expected deleted user to be unable to login, got {login_resp.status_code}: "
        f"{login_resp.text[:300]!r}"
    )
