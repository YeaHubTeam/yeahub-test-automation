"""UI subscription: fresh verified user per test (isolated T-Bank, no saved cards)."""

import pytest

from tests.mail.verified_user import yield_payment_link_subscriptions


@pytest.fixture
def payment_link_subscriptions(api_manager, verified_registered_user, get_list_subscriptions):
    yield from yield_payment_link_subscriptions(
        api_manager,
        user=verified_registered_user,
        subscriptions_catalog=get_list_subscriptions,
    )
