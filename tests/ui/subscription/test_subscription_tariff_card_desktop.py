"""Оформление подписки валидной картой через UI (desktop), Test IT [116].

https://team-vz1y.testit.software/browse/116

Полный путь: settings#select-tariff → модалка → T-Bank → активная подписка на stage.
Пользователь: API signUp + IMAP verify (`verified_registered_user`), teardown — delete user.
Отдельно от `test_subscription_payment_ui.py` (оплата по API-ссылке, `verified_registered_user`).
"""

import os
from typing import Any

import allure
import pytest
import testit
from playwright.sync_api import Page

from constants.constants import NAME_SUBSCRIPTIONS
from pages.auth.login_page import LoginPage
from pages.interview.interview_page import InterviewPage
from pages.payment.tbank_payment_page import TBankPaymentPage
from pages.settings.select_tariff_page import SelectTariffPage
from pages.subscription.subscription_checkout_modal import SubscriptionCheckoutModal
from payloads.card_payload import CardPayload
from tests.ui.flows.register_mail_interview_flow import require_mail_creds
from utils.reporting import report_step


@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.critical
@allure.epic("UI")
@allure.feature("Subscription")
@allure.story("Tariff checkout")
@allure.title("Оформление подписки с валидной банковской картой (desktop)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("component", "subscription")
@testit.workItemIds("13318a0e-49f0-4b32-bb8c-82cad5c473a1")
@testit.externalId("yeahub-ui-subscription-tariff-card-desktop-116")
@testit.title("Оформление подписки с валидной банковской картой (desktop)")
@testit.description(
    "ТК 116: signUp + IMAP verify → UI login → онбординг 1/5–5/5 → /settings#select-tariff → "
    "модалка → pay.tbank.ru → успешная оплата → активная подписка. Teardown: delete user."
)
@pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 (signUp + IMAP verify in fixture)",
)
def test_subscription_tariff_valid_card_desktop(
    page: Page,
    verified_registered_user: dict[str, Any],
):
    require_mail_creds()

    email = verified_registered_user["email"]
    password = verified_registered_user["password"]
    username = verified_registered_user["username"]

    login_page = LoginPage(page)
    interview_page = InterviewPage(page)
    tariff_page = SelectTariffPage(page)
    checkout_modal = SubscriptionCheckoutModal(page)
    payment_page = TBankPaymentPage(page)

    with report_step(
        "Предусловие 1: зарегистрированный пользователь без активной подписки",
        f"fixture verified_registered_user: signUp + verify email; тариф «{NAME_SUBSCRIPTIONS}» доступен",
    ):
        pass

    with report_step(
        "Предусловие 2: авторизация, онбординг и вкладка «Выбрать тариф»",
        "UI login → /interview → онбординг 1/5–5/5 → /settings#select-tariff; блок «Членство» с тарифами",
    ):
        login_page.open()
        login_page.fill_credentials(email, password)
        login_page.submit()
        interview_page.expect_authorized_after_login(username=username)
        interview_page.prepare_interview_after_login()
        interview_page.ensure_onboarding_completed_before_settings()
        tariff_page.open_select_tariff_ready()
        tariff_page.expect_membership_block_visible()

    with report_step(
        "Шаг 1: выбрать тариф и «Подписаться»",
        "Модальное окно оформления; отображается подтверждённый email пользователя",
    ):
        tariff_page.click_subscribe_on_tariff()
        checkout_modal.expect_opened_with_email(email)

    with report_step(
        "Шаг 2: отметить обязательные чекбоксы согласия",
        "Чекбоксы отмечены; кнопка «Подписаться» в модалке доступна",
    ):
        checkout_modal.check_required_consents()
        checkout_modal.expect_subscribe_enabled()

    with report_step(
        "Шаг 3: «Подписаться» в модалке",
        "Переход на страницу оплаты T-Bank (pay.tbank.ru)",
    ):
        checkout_modal.click_subscribe_and_expect_tbank()

    with report_step(
        "Шаги 4–5: валидная тестовая карта и «Оплатить»",
        "Форма заполнена; экран успешной оплаты",
    ):
        payment_page.assert_payment_form_opened()
        payment_page.fill_card(CardPayload.SUCCESS_CARD)
        payment_page.submit_payment()
        payment_page.assert_payment_success()

    with report_step(
        "Шаг 6: возврат в магазин",
        "Уход с pay.tbank.ru; редирект на yeahub.ru или yeatwork.ru (return URL платёжки)",
    ):
        payment_page.click_return_to_shop()
        payment_page.expect_left_tbank_after_return()

    with report_step(
        "Шаг 7: /settings#select-tariff на тестовом стенде",
        "Активная подписка: статус участника, оставшиеся дни, кнопка отмены",
    ):
        tariff_page.open_select_tariff_with_active_subscription()
        tariff_page.expect_active_subscription_visible()
