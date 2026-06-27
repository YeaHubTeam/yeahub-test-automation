import re

import pytest
from playwright.sync_api import Page, expect

from pages.interview.onboarding_modal import OnboardingModal

# На UI часто нет полной строки API «Премиум на 3 месяца» — матчим по фрагментам.
_PREMIUM_TARIFF_RE = re.compile(
    r"Премиум\s+на\s+3|Премиум.{0,30}3\s*месяц|3\s*месяц.{0,30}Премиум|1080|1\s*080",
    re.I,
)

# YH-2137: stage placeholder instead of tariff cards (TC 116 / nightly ui-payment).
# CLEANUP ticket for lead: remove this block when product restores select-tariff UI.
# Done when: /settings#select-tariff shows «Подписаться» on tariff cards AND
#   RUN_MAIL_INTEGRATION=1 pytest tests/ui/subscription/test_subscription_tariff_card_desktop.py -v --headed
#   passes without SKIPPED.
_TARIFF_UNAVAILABLE_RE = re.compile(
    r"информация о тарифах временно недоступна|tariffs?\s+(are\s+)?temporarily unavailable",
    re.I,
)
_TARIFF_STUB_SKIP_REASON = (
    "YH-2137: Tariff UI stub on stage (/settings#select-tariff). "
    "Create cleanup ticket to remove _skip_if_tariffs_temporarily_unavailable "
    "after product restores tariff cards (see TODO in select_tariff_page.py)."
)


class SelectTariffPage:
    """Раздел `/settings#select-tariff` — выбор тарифа и старт оформления подписки."""

    _TARIFF_PICKER_TITLE = re.compile(r"Членство|Membership", re.I)
    _ACTIVE_MEMBER_TITLE = re.compile(r"Участник\s+сообщества|Community\s+member", re.I)
    _DAYS_LEFT_RE = re.compile(r"Осталось\s+\d+\s+дн|осталось\s+\d+|days?\s+left", re.I)
    _SELECT_TARIFF_URL = re.compile(r".*/settings.*select-tariff", re.I)
    _SUBSCRIBE_BTN = re.compile(r"^Подписаться$|^Subscribe$", re.I)
    _SELECT_TARIFF_TAB = re.compile(r"выбрать\s+тариф|select\s+tariff|тариф", re.I)

    def __init__(self, page: Page):
        self.page = page

    def _onboarding_visible(self) -> bool:
        onboarding = OnboardingModal(self.page)
        if onboarding.modal.is_visible(timeout=800):
            return True
        return self.page.get_by_role("heading", name="Onboarding").is_visible(timeout=800)

    def _complete_onboarding_if_blocking(self) -> None:
        """Новый пользователь: Escape не закрывает — проходим 1/5–5/5."""
        if not self._onboarding_visible():
            onboarding = OnboardingModal(self.page)
            if not onboarding.modal.is_visible(timeout=5_000):
                return
        onboarding = OnboardingModal(self.page)
        onboarding.complete_onboarding_through_close()
        onboarding.expect_onboarding_dismissed()

    def _activate_select_tariff_tab(self) -> None:
        self._complete_onboarding_if_blocking()
        if self._subscribe_buttons_on_page().first.is_visible(timeout=2_000):
            return
        if self._is_active_subscription_ready(timeout_ms=1_000):
            return
        for test_id in ("Tabs_Item_select-tariff", "Tabs_Item_selectTariff"):
            tab = self.page.get_by_test_id(test_id)
            if tab.count() and tab.first.is_visible(timeout=1_000):
                if self._onboarding_visible():
                    self._complete_onboarding_if_blocking()
                tab.first.click(timeout=10_000)
                self._complete_onboarding_if_blocking()
                return
        tab_by_role = self.page.get_by_role("tab", name=self._SELECT_TARIFF_TAB)
        if tab_by_role.count():
            if self._onboarding_visible():
                self._complete_onboarding_if_blocking()
            tab_by_role.first.click(timeout=10_000)
            self._complete_onboarding_if_blocking()

    def _subscribe_buttons_on_page(self):
        return self.page.get_by_role("button", name=self._SUBSCRIBE_BTN).or_(
            self.page.get_by_text(self._SUBSCRIBE_BTN)
        )

    def open_select_tariff(self) -> None:
        self.page.goto(
            "/settings#select-tariff",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        expect(self.page).to_have_url(self._SELECT_TARIFF_URL, timeout=20_000)
        self._complete_onboarding_if_blocking()
        self._activate_select_tariff_tab()
        self._complete_onboarding_if_blocking()

    def open_select_tariff_ready(self) -> None:
        """Deep link + онбординг снимаем, пока недоступен блок тарифов."""
        for _ in range(12):
            self.open_select_tariff()
            self._skip_if_tariffs_temporarily_unavailable()
            if self._is_tariff_section_ready():
                return
            self._complete_onboarding_if_blocking()
            self.page.wait_for_timeout(400)
        self._skip_if_tariffs_temporarily_unavailable()
        self.expect_membership_block_visible()

    def open_select_tariff_with_active_subscription(self) -> None:
        """После оплаты: /settings#select-tariff и экран активной подписки."""
        for _ in range(12):
            self.open_select_tariff()
            if self._is_active_subscription_ready():
                return
            self._complete_onboarding_if_blocking()
            self.page.wait_for_timeout(400)
        self.expect_active_subscription_visible()

    def _is_active_subscription_ready(self, timeout_ms: int = 3_000) -> bool:
        if OnboardingModal(self.page).modal.is_visible(timeout=500):
            return False
        try:
            expect(self.page.get_by_text(self._ACTIVE_MEMBER_TITLE).first).to_be_visible(
                timeout=timeout_ms
            )
            return True
        except AssertionError:
            return False

    def _is_tariff_section_ready(self, timeout_ms: int = 3_000) -> bool:
        if OnboardingModal(self.page).modal.is_visible(timeout=500):
            return False
        try:
            expect(self._subscribe_buttons_on_page().first).to_be_visible(timeout=timeout_ms)
            return True
        except AssertionError:
            return False

    def _is_tariff_stub_visible(self) -> bool:
        return self.page.get_by_text(_TARIFF_UNAVAILABLE_RE).first.is_visible(timeout=2_000)

    def _skip_if_tariffs_temporarily_unavailable(self) -> None:
        """Runtime skip while stage shows tariff placeholder (YH-2137).

        TODO YH-2137: delete this method, _TARIFF_UNAVAILABLE_RE and _TARIFF_STUB_SKIP_REASON
        after product task «restore tariffs on stage» is Done and TC 116 passes locally.
        """
        if self._is_tariff_stub_visible():
            pytest.skip(_TARIFF_STUB_SKIP_REASON)

    def expect_membership_block_visible(self) -> None:
        """Тарифы для оформления: блок членства и хотя бы одна кнопка «Подписаться»."""
        self._skip_if_tariffs_temporarily_unavailable()
        expect(self.page.get_by_text(self._TARIFF_PICKER_TITLE).first).to_be_visible(timeout=15_000)
        expect(self._subscribe_buttons_on_page().first).to_be_visible(timeout=20_000)

    def click_subscribe_on_tariff(self) -> None:
        """Шаг 1 ТК 116: «Подписаться» у тарифа «Премиум на 3 месяца» (не в модалке)."""
        self._complete_onboarding_if_blocking()
        subscribe_in_card = (
            self.page.locator("div, section, article, li")
            .filter(has_text=_PREMIUM_TARIFF_RE)
            .filter(has=self.page.get_by_role("button", name=self._SUBSCRIBE_BTN))
            .get_by_role("button", name=self._SUBSCRIBE_BTN)
            .first
        )
        if not subscribe_in_card.count():
            subscribe_in_card = (
                self.page.locator("div, section, article, li")
                .filter(has_text=re.compile(r"3\s*мес|1080", re.I))
                .filter(has=self.page.get_by_role("button", name=self._SUBSCRIBE_BTN))
                .get_by_role("button", name=self._SUBSCRIBE_BTN)
                .first
            )
        expect(subscribe_in_card).to_be_visible(timeout=20_000)
        subscribe_in_card.scroll_into_view_if_needed()
        expect(subscribe_in_card).to_be_enabled(timeout=10_000)
        subscribe_in_card.click(timeout=15_000)

    def expect_active_subscription_visible(self) -> None:
        """Шаг 7 ТК 116: статус участника, оставшиеся дни; отмена — если доступна в UI."""
        expect(self.page.get_by_text(self._ACTIVE_MEMBER_TITLE).first).to_be_visible(timeout=25_000)
        expect(self.page.get_by_text(self._DAYS_LEFT_RE).first).to_be_visible(timeout=20_000)
        cancel_btn = self.page.get_by_role(
            "button",
            name=re.compile(r"отмен.*подписк|cancel\s+subscription", re.I),
        )
        if cancel_btn.count():
            expect(cancel_btn.first).to_be_visible(timeout=10_000)
