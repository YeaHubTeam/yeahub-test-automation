from __future__ import annotations
import time
from collections.abc import Callable
from typing import Any
import requests

_TRANSIENT_NETWORK_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)

DEFAULT_MAX_ATTEMPTS = 5

def default_backoff(attempt: int) -> float:
    return 2 * (attempt + 1)

def request_with_retries(
        request_fn: Callable[[], requests.Response],
        *,
        success_status: int | set[int] = 201,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff: Callable[[int], float] = default_backoff,
        on_retry: Callable[[int, requests.Response], None] | None = None,
    ) -> requests.Response:
    success_set = {success_status} if isinstance(success_status, int) else
    set(success_status)
    last_response: requests.Response | None = None

    for attempt in range(max_attempts):
        try:
            last_response = request_fn()
        except _TRANSIENT_NETWORK_ERRORS as exc:
            if attempt == max_attempts - 1:
                raise
            time.sleep(backoff(attempt))
            continue

        if last_response.status_code in success_set:
            return last_response

        if last_response.status_code >= 500 and attempt < max_attempts - 1:
            if on_retry:
                on_retry(attempt, last_response)
            time.sleep(backoff(attempt))
            continue

        # 4xx или последняя попытка - не ретраим, возвращаем как есть
        return last_response

    assert last_response is not None
    return last_response
