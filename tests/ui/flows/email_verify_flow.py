"""UI-поток верификации email по ссылке из IMAP (ТК 422, шаги 4–5)."""

import re

from playwright.sync_api import Page, expect

_VERIFY_SUCCESS_RE = re.compile(
    r"Email\s+verified\s+successfully|You\s+will\s+be\s+redirected",
    re.I,
)
_STALE_TOKEN_RE = re.compile(
    r"email_verification_token\.incorrect|click on the link from the last email",
    re.I,
)
_APP_ORIGIN_RE = re.compile(r"yeatwork\.ru", re.I)


def open_verification_link_in_new_tab(page: Page, verification_url: str) -> Page:
    """Шаг 5: открыть ссылку из письма в новой вкладке, дождаться success + редирект."""
    with page.context.expect_page() as new_page_info:
        page.evaluate("url => window.open(url)", verification_url)
    verify_page = new_page_info.value
    verify_page.wait_for_load_state("domcontentloaded", timeout=60_000)
    page_text = verify_page.locator("body").inner_text(timeout=5_000)
    if _STALE_TOKEN_RE.search(page_text):
        raise AssertionError(
            "Verification link token is stale (not from the latest email). "
            "Backend returned auth.user.email_verification_token.incorrect."
        )
    expect(verify_page.get_by_text(_VERIFY_SUCCESS_RE).first).to_be_visible(timeout=20_000)
    expect(verify_page).to_have_url(_APP_ORIGIN_RE, timeout=20_000)
    verify_page.close()
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    return verify_page
