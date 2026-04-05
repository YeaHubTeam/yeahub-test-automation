import pytest

from mail.parsers import extract_verification_link


pytestmark = [pytest.mark.api, pytest.mark.regression]


def test_extract_verification_link_prefers_verification_link():
    text = """
    Скачайте Outlook для iOS<https://aka.ms/o0ukef>
    Подтвердить Email<https://api.yeatwork.ru/auth/verify-email?token=123>
    """
    html = """
    <a href="https://aka.ms/o0ukef">Outlook for iOS</a>
    <a href="https://api.yeatwork.ru/auth/verify-email?token=123">Подтвердить Email</a>
    """

    result = extract_verification_link(text=text, html=html)

    assert result == "https://api.yeatwork.ru/auth/verify-email?token=123"


def test_extract_verification_link_returns_none_without_verification_link():
    text = "https://example.com/page"
    html = '<a href="https://example.com/page">Example</a>'

    result = extract_verification_link(text=text, html=html)

    assert result is None


def test_extract_verification_link_finds_verification_link_in_plain_text():
    text = "Подтвердить Email: https://api.yeatwork.ru/auth/verify-email?token=abc"

    result = extract_verification_link(text=text)

    assert result == "https://api.yeatwork.ru/auth/verify-email?token=abc"
