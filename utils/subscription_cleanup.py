"""Очистка подписки «Премиум на 3 месяца» у static_user перед/после UI/API payment-тестов."""

import time

from constants.constants import NAME_SUBSCRIPTIONS
from models.Subscriptions.model_user_subsriptions import UserSubscriptionResponse
from utils.helpers import DataUtils


def premium_tariff_id(subscriptions_catalog) -> int:
    return DataUtils.find_item(
        items=subscriptions_catalog,
        condition=lambda sub: sub.name == NAME_SUBSCRIPTIONS,
        transform=lambda sub: sub.id,
    )


def delete_user_premium_subscription_if_present(
    api_manager,
    *,
    user_id: str,
    subscriptions_catalog,
    expected_delete_status=None,
) -> None:
    """Удалить pending_payment/active подписку «Премиум на 3 месяца», если есть."""
    tariff_id = premium_tariff_id(subscriptions_catalog)
    last_existing = None
    for attempt in range(5):
        last_existing = api_manager.subscriptions_api.get_subscriptions_users(
            user_id, expected_status=[200, 503]
        )
        if last_existing.status_code == 200:
            break
        time.sleep(2 * (attempt + 1))

    if last_existing is None or last_existing.status_code != 200:
        return

    validated = DataUtils.type_adapter(list[UserSubscriptionResponse], last_existing.json())
    row = DataUtils.find_item(
        items=validated,
        condition=lambda sub: (
            sub.subscription_id == tariff_id
            and sub.state in ["pending_payment", "active", "canceled", "inactive"]
        ),
    )
    if not row:
        return

    cleanup_body = {
        "subscriptionId": tariff_id,
        "userId": user_id,
        "orderId": row.id,
    }
    api_manager.subscriptions_api.delete_subscriptions(
        cleanup_body,
        expected_status=expected_delete_status or [200, 404],
    )
