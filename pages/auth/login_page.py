import re

from playwright.sync_api import expect


class LoginPage:
    """UI-логин (поле username = email, см. README и API login)."""

    def __init__(self, page):
        self.page = page

    def open(self) -> None:
        self.page.goto("/auth/login", wait_until="domcontentloaded", timeout=60_000)
        expect(self.page.locator('input[name="username"]')).to_be_visible(timeout=15_000)

    def fill_credentials(self, email: str, password: str) -> None:
        self.page.locator('input[name="username"]').fill(email)
        self.page.locator('input[type="password"]').fill(password)

    def submit(self) -> None:
        self.page.get_by_role("button", name=re.compile(r"Войти|Вход|Sign\s*in", re.I)).click()
