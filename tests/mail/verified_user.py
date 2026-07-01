"""signUp + IMAP verify for subscription/payment integration tests (no shared static account)."""

from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Any

import pytest
import requests

from api.api_manager import ApiManager
from tests.mail.signup_retry import (
    authenticate_with_retries,
    register_user_with_retries,
    request_with_integration_retries,
)
from tests.mail.verification_flow import profile_user_id, verify_api_registered_user_email
from tests.ui.flows.register_mail_interview_flow import new_plus_tagged_email, require_mail_creds
from utils.data_generator import DataGenerator
from utils.helpers import DataUtils
from utils.subscription_cleanup import delete_user_premium_subscription_if_present


def _base_user_payload(*, email: str, password: str, username: str) -> dict[str, Any]:
    return {
        "username": username,
        "password": password,
        "email": email,
        "phone": DataGenerator.random_phone(),
        "country": DataGenerator.random_country(),
        "city": DataGenerator.random_city(),
        "birthday": DataGenerator.random_birthday(),
        "address": DataGenerator.random_address(),
        "avatarUrl": None,
    }


def provision_verified_mail_user(
    api_manager: ApiManager,
    *,
    user_payload: dict[str, Any] | None = None,
    mail_state: dict[str, Any] | None = None,
    on_signup_retry: Callable[[int, requests.Response], None] | None = None,
) -> dict[str, Any]:
    """Register on MAIL_EMAIL+tag, verify via IMAP, return user dict with id/token."""
    require_mail_creds()
    started_at, _tag, recipient_email, password, username = new_plus_tagged_email()
    if mail_state is not None:
        mail_state["started_at"] = started_at

    if user_payload is None:
        user = _base_user_payload(email=recipient_email, password=password, username=username)
    else:
        user = user_payload
        user["email"] = recipient_email
        user["password"] = password
        user["username"] = username

    def _default_on_retry(_attempt: int, _response: requests.Response) -> None:
        nonlocal started_at
        new_started_at, _new_tag, new_email, new_password, new_username = new_plus_tagged_email()
        started_at = new_started_at
        if mail_state is not None:
            mail_state["started_at"] = new_started_at
        user["email"] = new_email
        user["password"] = new_password
        user["username"] = new_username

    retry_handler = on_signup_retry or _default_on_retry

    last_response = register_user_with_retries(api_manager, user, on_retry=retry_handler)
    if last_response.status_code == 503:
        pytest.skip("signUp unavailable (503) after retries — transient stage overload")
    assert last_response.status_code == 201, "signUp is unavailable (503) after retries"

    user["id"] = last_response.json().get("user", {}).get("id")
    user["token"] = last_response.json().get("access_token")
    verify_started_at = mail_state["started_at"] if mail_state is not None else started_at
    authenticate_with_retries(api_manager, user["email"], user["password"])
    user_id = profile_user_id(api_manager.auth_api.profile().json())
    verify_api_registered_user_email(
        api_manager,
        email=user["email"],
        password=user["password"],
        user_id=user_id,
        started_at=verify_started_at,
    )
    return user


def yield_payment_link_subscriptions(
    api_manager: ApiManager,
    *,
    user: dict[str, Any],
    subscriptions_catalog,
) -> Generator[str, None, None]:
    """Create payment/init link; cleanup premium pending subscription before and after."""
    user_id = user["id"]
    user_email = user["email"]
    delete_user_premium_subscription_if_present(
        api_manager, user_id=user_id, subscriptions_catalog=subscriptions_catalog
    )
    id_subscriptions = DataUtils.find_item(
        items=subscriptions_catalog,
        condition=lambda sub: sub.name == "Премиум на 3 месяца",
        transform=lambda sub: sub.id,
    )

    last_response = request_with_integration_retries(
        lambda: api_manager.subscriptions_api.subscriptions_payment_pending(
            id_subscriptions,
            user_email,
            expected_status=[200, 503],
        ),
    )
    assert last_response.status_code == 200, "payment/init is unavailable (503) after retries"

    payment_url = last_response.text
    yield payment_url
    delete_user_premium_subscription_if_present(
        api_manager, user_id=user_id, subscriptions_catalog=subscriptions_catalog
    )
