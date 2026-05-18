import os

import pytest

APP_BASE_URL = os.getenv("APP_BASE_URL", "https://app.yeatwork.ru")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "base_url": APP_BASE_URL,
    }
