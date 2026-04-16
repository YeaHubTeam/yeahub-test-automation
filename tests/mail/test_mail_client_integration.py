import os

import allure
import pytest

from mail.mail_client import MailClient
from resources.mail_creds import MailCreds

pytestmark = [
    pytest.mark.api,
    pytest.mark.regression,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_MAIL_INTEGRATION") != "1",
        reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
    ),
]


@allure.epic("Тест - Письмо верификации")
@allure.title("Проверка живого flow письма верификации")
def test_verification_email_flow_integration():
    with allure.step("Создаём клиент для mailbox.org"):
        client = MailClient(
            host=MailCreds.HOST,
            email=MailCreds.EMAIL,
            password=MailCreds.PASSWORD,
            folder=MailCreds.FOLDER,
            port=MailCreds.PORT,
        )

    with allure.step("Ищем письмо с темой Verify Your Email"):
        found_message = client.find_message(subject="Verify Your Email")

    with allure.step("Проверяем, что письмо найдено"):
        assert found_message is not None, "Verification email was not found"

    with allure.step("Извлекаем ссылку подтверждения"):
        verification_link = client.get_message_link(found_message)

    with allure.step("Проверяем, что ссылка подтверждения найдена"):
        assert verification_link is not None, "Verification link was not extracted"
        assert "verify-email" in verification_link

    with allure.step("Удаляем письмо по uid"):
        uid = found_message.uid
        client.delete_message(uid)

    with allure.step("Проверяем, что письмо больше не осталось в ящике"):
        remaining_uids = {message.uid for message in client.get_messages()}

        assert uid not in remaining_uids
