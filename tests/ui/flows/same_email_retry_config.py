"""Параметры хвоста «повторная регистрация на тот же email» в `test_register_and_verify_email_e2e`.

Дефолты совпадают с CI / ручным прогоном полного ТК. Переопределение — только через env при необходимости.
"""

import os

# Совпадают с прежними рекомендациями в README / integration.yml (дублировать в workflow не обязательно).
DEFAULT_SAME_EMAIL_MAX_WAIT_SECONDS = 120
DEFAULT_POLL_INTERVAL_SECONDS = 4.0
POLL_CLAMP_MIN = 3.0
POLL_CLAMP_MAX = 5.0


def _int_env(name: str, default: int = 0) -> int:
    raw = os.getenv(name, str(default) if default else "").strip()
    if raw == "":
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def same_email_retry_max_wait_seconds() -> int:
    """Бюджет ожидания перед одним UI submit на тот же email.

    1. Если задан `REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS` (в т.ч. `0`) — он.
    2. Иначе если задан legacy `REGISTER_SAME_EMAIL_RETRY_AFTER_SECONDS` — он.
    3. Иначе дефолт **120** (полный хвост без экспорта в терминале).

    Быстрый путь (только тост): `REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS=0`.
    """
    if os.getenv("REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS", "").strip() != "":
        return _int_env("REGISTER_SAME_EMAIL_RETRY_MAX_WAIT_SECONDS", 0)
    if os.getenv("REGISTER_SAME_EMAIL_RETRY_AFTER_SECONDS", "").strip() != "":
        return _int_env("REGISTER_SAME_EMAIL_RETRY_AFTER_SECONDS", 0)
    return DEFAULT_SAME_EMAIL_MAX_WAIT_SECONDS


def same_email_retry_poll_interval_seconds() -> float:
    """Длительность одного куска ожидания (сек), по умолчанию 4, clamp 3–5."""
    raw = os.getenv("REGISTER_SAME_EMAIL_RETRY_POLL_INTERVAL_SECONDS", "").strip()
    if raw == "":
        v = DEFAULT_POLL_INTERVAL_SECONDS
    else:
        try:
            v = float(raw.replace(",", "."))
        except ValueError:
            v = DEFAULT_POLL_INTERVAL_SECONDS
    return min(POLL_CLAMP_MAX, max(POLL_CLAMP_MIN, v))
