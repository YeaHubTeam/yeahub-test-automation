"""Проверки состояния профиля (verified / specialization) — без polling, один запрос + assert."""

from api.api_manager import ApiManager
from tests.mail.signup_retry import authenticate_with_retries


def profile_user_id(profile: dict) -> str:
    user = profile.get("user")
    if isinstance(user, dict) and user.get("id") is not None:
        return str(user["id"])
    assert profile.get("id") is not None, "user id missing in profile response"
    return str(profile["id"])


def profile_is_verified(profile: dict) -> bool:
    user = profile.get("user")
    if isinstance(user, dict) and "isVerified" in user:
        return user["isVerified"] is True
    return profile.get("isVerified") is True


def assert_profile_verified(api_manager: ApiManager, email: str, password: str) -> None:
    authenticate_with_retries(api_manager, email, password)
    profile = api_manager.auth_api.profile().json()
    assert profile_is_verified(profile), "User email is not verified after verification link"


def assert_profile_not_verified(api_manager: ApiManager, email: str, password: str) -> None:
    authenticate_with_retries(api_manager, email, password)
    profile = api_manager.auth_api.profile().json()
    assert not profile_is_verified(profile), (
        "Expected isVerified=false before opening verification link"
    )


def assert_profile_specialization_selected(
        api_manager: ApiManager, email: str, password: str
) -> None:
    """После онбординга в профиле должна быть выбранная специализация (specializationId != 0)."""
    authenticate_with_retries(api_manager, email, password)
    profile = api_manager.auth_api.profile().json()
    profiles = profile.get("profiles") or []
    assert profiles, "profiles missing in /auth/profile"
    sid = profiles[0].get("specializationId")
    assert sid not in (None, 0), f"expected specializationId set after onboarding, got {sid!r}"