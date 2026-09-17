"""ВНИМАНИЕ: этот тест написан под Appium (driver.find_element("accessibility id", ...)),
а не под Playwright, который используется во всём остальном проекте.

Отсюда постоянная ошибка во всех прогонах: `fixture 'driver' not found` —
фикстуры `driver` в проекте нет и никогда не было, только Playwright `page`.

Часть шагов — заглушки (`# TODO: заменить на твой старт приложения`, пустой `pass`
вместо реальной проверки в шаге 8). Файл закарантинен, чтобы не шуметь ошибкой
в каждом прогоне, пока не будет принято решение:
  - настроить Appium-раннер для iOS и довести тест до рабочего вида, либо
  - переписать сценарий под Playwright (mobile emulation / отдельный runner).

TODO: завести тикет на восстановление iOS-покрытия forgot-password и вписать сюда номер.
"""

from datetime import datetime, timezone

import allure
import pytest

from api.api_manager import ApiManager
from tests.mail.reset_password_flow import wait_imap_reset_password_link_after_ui_send
from utils.data_generator import DataGenerator

pytestmark = pytest.mark.skip(
    reason=(
        "Написан под Appium (driver.find_element), а не Playwright — падает с "
        "'fixture driver not found' в каждом прогоне. Требует Appium-раннера или "
        "переписывания под текущий стек. См. TODO в шапке файла."
    )
)


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Auth")
@allure.story("Forgot password recovery (iOS)")
@allure.title("Восстановление пароля через письмо (iOS)")
@allure.severity(allure.severity_level.CRITICAL)
def test_forgot_password_recovery_ios(
    driver,
    api_manager: ApiManager,
    verified_registered_user: dict,
):
    email = verified_registered_user["email"]
    username = verified_registered_user["username"]
    new_password = DataGenerator.random_password()

    # =========================
    # STEP 1: открыть login экран
    # =========================
    with allure.step("Открыть экран логина"):
        # TODO: заменить на твой старт приложения
        driver.find_element("accessibility id", "login_screen")

    # =========================
    # STEP 2: нажать Forgot password
    # =========================
    with allure.step("Перейти в Forgot Password"):
        driver.find_element("accessibility id", "forgot_password_button").click()

    # =========================
    # STEP 3: ввести email
    # =========================
    with allure.step("Ввести email"):
        driver.find_element("accessibility id", "forgot_email_input").send_keys(email)

    # =========================
    # STEP 4: отправить письмо
    # =========================
    with allure.step("Отправить запрос восстановления"):
        driver.find_element("accessibility id", "forgot_submit_button").click()

        sent_after = datetime.now(timezone.utc)

    # =========================
    # STEP 5: получить ссылку из IMAP
    # =========================
    with allure.step("Получить ссылку восстановления из email"):
        recovery_url = wait_imap_reset_password_link_after_ui_send(
            api_manager,
            email=email,
            since=sent_after,
        )

    # =========================
    # STEP 6: открыть recovery link (deep link / webview)
    # =========================
    with allure.step("Открыть recovery ссылку"):
        driver.get(recovery_url)

    # =========================
    # STEP 7: установить новый пароль
    # =========================
    with allure.step("Установить новый пароль"):
        driver.find_element("accessibility id", "new_password_input").send_keys(new_password)
        driver.find_element("accessibility id", "confirm_password_input").send_keys(new_password)

        driver.find_element("accessibility id", "save_password_button").click()

    # =========================
    # STEP 8: проверка успешного изменения
    # =========================
    with allure.step("Проверить успешное восстановление"):
        # например toast или redirect
        # driver.find_element("accessibility id", "success_toast")

        pass

    # =========================
    # STEP 9: login с новым паролем
    # =========================
    with allure.step("Логин с новым паролем"):
        driver.find_element("accessibility id", "login_email").send_keys(email)
        driver.find_element("accessibility id", "login_password").send_keys(new_password)
        driver.find_element("accessibility id", "login_submit").click()

    # =========================
    # STEP 10: финальная проверка
    # =========================
    with allure.step("Проверить авторизацию"):
        driver.find_element("accessibility id", "interview_screen")

    verified_registered_user["active_password"] = new_password
