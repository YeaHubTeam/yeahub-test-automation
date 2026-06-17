"""Allure + Test IT step reporting for UI/e2e tests."""

from collections.abc import Iterator
from contextlib import contextmanager

import allure
import testit


@contextmanager
def report_step(title: str, description: str | None = None) -> Iterator[None]:
    """One step in Allure report and Test IT autotest description (importRealtime)."""
    with allure.step(title):
        if description:
            with testit.step(title, description):
                yield
        else:
            with testit.step(title):
                yield
