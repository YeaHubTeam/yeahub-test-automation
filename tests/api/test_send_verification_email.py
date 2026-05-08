import allure
import pytest

from api.api_manager import ApiManager

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.smoke,
    pytest.mark.pr_safe,
]


@allure.epic("Тест - Отправка емейла верификации")
@pytest.mark.api
class TestSendVerificationEmailYeahub:
    def test_send_verification_email(self, api_manager: ApiManager, logged_in_user):
        # В PR-safe контуре проверяем только доступность ручки.
        # Backend может ограничивать частоту отправки (rate limit) и возвращать 403 limited_period.
        response = api_manager.auth_api.send_verification_email(
            logged_in_user, expected_status=[200, 403]
        )

        if response.status_code == 200:
            payload = response.json()
            assert "sent" in str(payload.get("message", "")).lower()
            return

        payload = response.json()
        assert payload.get("message") == "user.user.email.limited_period"
