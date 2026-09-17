"""Временное управление сессией: снятие Bearer/cookies для анонимных проверочных запросов.

Нужен там, где надо постучаться в API "как аноним" (повторный логин при teardown,
проверка гонки регистрации с тем же email), не потеряв текущую авторизацию
основного тестового пользователя.
"""

from contextlib import contextmanager

from requests.utils import add_dict_to_cookiejar, dict_from_cookiejar

from api.api_manager import ApiManager


def snapshot_authorization_headers(api_manager: ApiManager) -> tuple[str | None, str | None]:
    session_auth = api_manager.session.headers.get("Authorization")
    api_auth = api_manager.auth_api.headers.get("Authorization")
    return session_auth, api_auth


def clear_authorization_headers(api_manager: ApiManager) -> None:
    api_manager.session.headers.pop("Authorization", None)
    api_manager.auth_api.headers.pop("Authorization", None)


def apply_authorization_headers(
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


def snapshot_session_cookies(api_manager: ApiManager) -> dict:
    return dict_from_cookiejar(api_manager.session.cookies)


def restore_session_cookies(api_manager: ApiManager, cookies_dict: dict) -> None:
    api_manager.session.cookies.clear()
    if cookies_dict:
        add_dict_to_cookiejar(api_manager.session.cookies, cookies_dict)


@contextmanager
def anonymous_session(api_manager: ApiManager):
    """Временно снять Authorization и cookies на время блока, затем вернуть как было.

    Раньше этот snapshot/clear/restore паттерн был скопирован вручную в трёх местах
    в verification_flow.py — здесь он один.
    """
    saved_session, saved_api = snapshot_authorization_headers(api_manager)
    saved_cookies = snapshot_session_cookies(api_manager)
    clear_authorization_headers(api_manager)
    api_manager.session.cookies.clear()
    try:
        yield
    finally:
        restore_session_cookies(api_manager, saved_cookies)
        apply_authorization_headers(api_manager, saved_session, saved_api)