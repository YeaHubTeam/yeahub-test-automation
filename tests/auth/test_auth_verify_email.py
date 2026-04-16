import pytest

from api.api_manager import ApiManager


# TODO - ТЕСТ ТРЕБУЕТ ДОРАБОТКИ! НЕ ГОТОВО! Жду таск - https://tracker.yandex.ru/YH-1756
@pytest.mark.skip(reason="Нужен мейлер клиент - Ждем таск: https://tracker.yandex.ru/YH-1756")
class TestVerifyEmailYeahub:
    def test_auth_verify_email(self, api_manager: ApiManager, verify_email_user):
        response = api_manager.auth_api.verify_sent_email(verify_email_user)
        print(response)
