from api.api_manager import ApiManager
import allure
import pytest

''' ТЕСТ ТРЕБУЕТ ДОРАБОТКИ! НЕ ГОТОВО! Жду таск - https://tracker.yandex.ru/YH-1738 
 
@allure.epic('Тест - Отправка емейла верификации')
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.xfail('НЕ РАБОЧИЙ ТЕСТ! НЕ ЗАПУСКАТЬ ПОКА')
class TestSendVerificationEmailYeahub:
    def test_send_verification_email(self, api_manager: ApiManager, logged_in_user):
        response = api_manager.auth_api.send_verification_email(logged_in_user)

        assert response.status_code == 200

'''
