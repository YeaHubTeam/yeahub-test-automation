"""Backward-compat facade поверх tests.mail.verification.*

Модуль разбит на компоненты с одной ответственностью:
    tests/mail/verification/
        session_context.py   — анонимные запросы (снятие/восстановление auth)
        actions.py            — одноразовые действия с ретраями (send/confirm email)
        polling.py             — циклы ожидания (IMAP, verified-профиль, гонка регистрации)
        asserts.py              — проверки состояния профиля
        user_preparation.py      — payload для signUp + оркестрация верификации
        cleanup.py                — teardown (логин + удаление пользователя)

Этот файл оставлен для обратной совместимости со старыми
`from tests.mail.verification_flow import ...` — в новом коде импортируй
напрямую из tests.mail.verification.<module>.
"""

from tests.mail.verification.actions import (
    confirm_email_via_link,
    send_verification_email_with_retries,
)
from tests.mail.verification.asserts import (
    assert_profile_not_verified,
    assert_profile_specialization_selected,
    assert_profile_verified,
    profile_is_verified,
    profile_user_id,
)
from tests.mail.verification.cleanup import (
    TeardownAuthResult,
    authenticate_for_teardown,
    delete_authenticated_user_via_api,
)
from tests.mail.verification.polling import (
    wait_imap_verification_link,
    wait_imap_verification_link_or_resend,
    wait_same_email_signup_ready_via_api_probe,
    wait_until_profile_verified,
)
from tests.mail.verification.user_preparation import (
    build_signup_payload_for_api,
    same_email_signup_api_probe_enabled,
    verify_api_registered_user_email,
)

__all__ = [
    "confirm_email_via_link",
    "send_verification_email_with_retries",
    "assert_profile_not_verified",
    "assert_profile_specialization_selected",
    "assert_profile_verified",
    "profile_is_verified",
    "profile_user_id",
    "TeardownAuthResult",
    "authenticate_for_teardown",
    "delete_authenticated_user_via_api",
    "wait_imap_verification_link",
    "wait_imap_verification_link_or_resend",
    "wait_same_email_signup_ready_via_api_probe",
    "wait_until_profile_verified",
    "build_signup_payload_for_api",
    "same_email_signup_api_probe_enabled",
    "verify_api_registered_user_email",
]