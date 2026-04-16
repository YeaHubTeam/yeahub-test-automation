import allure
import pytest

from api.api_manager import ApiManager

# TODO ТЕСТ ТРЕБУЕТ ДОРАБОТКИ! НЕ ГОТОВО!


@allure.epic("Тест - сброса пароля")
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.skip(reason="Нужен мейлер клиент - Ждем таск: https://tracker.yandex.ru/YH-1756")
class TestResetPasswordYeahub:
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("AQA_Engineer", "Nikolay_Martoplyas")
    @allure.title("Тестирование сброса пароля пользователя")
    def test_patch_reset_password_positive(self, api_manager: ApiManager, registered_user):
        with allure.step("Оправляем PATCH запрос на сброс текущего пароля пользователя"):
            response = api_manager.auth_api.reset_password(registered_user)

        with allure.step("Проверяем успешность статус кода ответа = 200"):
            assert response.status_code == 200
