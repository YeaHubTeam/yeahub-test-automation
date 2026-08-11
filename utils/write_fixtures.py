from typing import Any

from api.api_manager import ApiManager
from tests.mail.signup_retry import register_user_with_retries
from tests.mail.verification_flow import assert_profile_not_verified, authenticate_for_teardown
from tests.mail.verified_user import provision_verified_mail_user
from tests.ui.flows.register_mail_interview_flow import new_plus_tagged_email, require_mail_creds
from utils.data_generator import DataGenerator


def cleanup_user(api_manager: ApiManager, test_user: dict) -> None:
    """Teardown: login с active_password (если меняли) или исходным паролем → delete_user."""
    user_id = test_user.get("id")
    if not user_id:
        return

    email = test_user.get("email")
    password = test_user.get("password")
    active_password = test_user.get("active_password")

    candidates: list[str] = []
    for pwd in (active_password, password):
        if pwd and pwd not in candidates:
            candidates.append(pwd)
    for pwd in candidates:
        auth_result = authenticate_for_teardown(api_manager, email, pwd)
        if auth_result in ("auth_failed", "transient_failed"):
            continue
        delete_resp = api_manager.user_api.delete_user(user_id, expected_status=[200, 204, 404])
        if delete_resp.status_code in (200, 204, 404):
            return


def create_registered_user(api_manager: ApiManager, user: dict) -> dict:
    def _refresh_identity(_attemp: int, _response) -> None:
        user["email"] = DataGenerator.random_email()
        user["username"] = DataGenerator.random_username()

    response = register_user_with_retries(api_manager, user, on_retry=_refresh_identity)
    assert response.status_code == 201, "signUp is unavailable (503) after retries"

    user["id"] = response.json().get("user", {}).get("id")
    user["token"] = response.json().get("access_token")
    return user


def _make_mail_identity_refresher(mail_identity: dict, test_user: dict):
    """Фабрика, создает closure для on_retry, привязанный к конкректным
    mail_identity/test_user."""

    def _refresh(_attempt: int, _response) -> None:
        new_started_at, _tag, new_email, new_password, new_username = new_plus_tagged_email()
        mail_identity["started_at"] = new_started_at
        test_user["email"] = new_email
        test_user["password"] = new_password
        test_user["username"] = new_username

    return _refresh


def create_unverified_mail_registered_user(api_manager: ApiManager, test_user: dict) -> dict:
    """API signUp на MAIL_EMAIL+tag, isVerified=false. Для UI ТК 422 (IMAP verify)."""
    require_mail_creds()

    mail_identity: dict = {"started_at": None}
    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()
    mail_identity["started_at"] = started_at
    test_user["email"] = recipient_email
    test_user["password"] = password
    test_user["username"] = username

    _refresh_mail_identity = _make_mail_identity_refresher(mail_identity, test_user)

    last_response = register_user_with_retries(
        api_manager, test_user, on_retry=_refresh_mail_identity
    )
    assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

    test_user["id"] = last_response.json().get("user", {}).get("id")
    test_user["token"] = last_response.json().get("access_token")
    test_user["mail_since"] = mail_identity["started_at"]
    assert_profile_not_verified(api_manager, test_user["email"], test_user["password"])
    return test_user


def create_verified_mail_registered_user(api_manager: ApiManager, test_user: dict) -> dict:
    """signUp → IMAP verify → teardown delete. Для mail/UI с `isVerified=true` (не для TC 113).
    Email — `local+tag@domain` на MAIL_EMAIL (иначе IMAP не найдёт письмо верификации).
    """
    mail_identity: dict = {"started_at": None}
    refresh_mail_identity = _make_mail_identity_refresher(mail_identity, test_user)

    provision_verified_mail_user(
        api_manager,
        user_payload=test_user,
        mail_state=mail_identity,
        on_signup_retry=refresh_mail_identity,
    )
    return test_user
