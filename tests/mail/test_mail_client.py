from datetime import datetime, timezone

import pytest

from mail.exceptions import MessageNotFoundError, VerificationLinkNotFoundError
from mail.mail_client import MailClient
from mail.models import MailMessage


pytestmark = [pytest.mark.unit, pytest.mark.regression]


def test_find_message_returns_newest_matching_message(monkeypatch):
    messages = [
        MailMessage(
            uid="1",
            subject="Fw: Verify Your Email",
            sender="yeahub@yeahub.ru",
            date=datetime(2026, 4, 4, 19, 58, 0, tzinfo=timezone.utc),
            body="old message",
            html=None,
        ),
        MailMessage(
            uid="2",
            subject="Verify Your Email",
            sender="yeahub@yeahub.ru",
            date=datetime(2026, 4, 5, 11, 54, 19, tzinfo=timezone.utc),
            body="new message",
            html=None,
        ),
        MailMessage(
            uid="3",
            subject="Some other email",
            sender="noreply@example.com",
            date=datetime(2026, 4, 5, 12, 0, 0, tzinfo=timezone.utc),
            body="other message",
            html=None,
        ),
    ]

    monkeypatch.setattr(MailClient, "get_messages", lambda self: messages)

    client = MailClient(
        host="imap.example.com",
        email="user@example.com",
        password="password",
    )

    message = client.find_message(subject="Verify Your Email")

    assert message is not None
    assert message.uid == "2"
    assert message.subject == "Verify Your Email"


def test_find_message_raises_when_no_match(monkeypatch):
    messages = [
        MailMessage(
            uid="1",
            subject="Welcome to mailbox",
            sender="noreply@mailbox.org",
            date=datetime(2026, 4, 4, 19, 58, 0, tzinfo=timezone.utc),
            body="welcome message",
            html=None,
        ),
        MailMessage(
            uid="2",
            subject="Another random email",
            sender="noreply@example.com",
            date=datetime(2026, 4, 5, 11, 54, 19, tzinfo=timezone.utc),
            body="another message",
            html=None,
        ),
    ]

    monkeypatch.setattr(MailClient, "get_messages", lambda self: messages)

    client = MailClient(
        host="imap.example.com",
        email="user@example.com",
        password="password",
    )

    with pytest.raises(MessageNotFoundError):
        client.find_message(subject="Verify Your Email")


def test_find_message_raises_when_body_does_not_match(monkeypatch):
    messages = [
        MailMessage(
            uid="1",
            subject="Fw: Verify Your Email",
            sender="yeahub@yeahub.ru",
            date=datetime(2026, 4, 5, 11, 54, 19, tzinfo=timezone.utc),
            body="This email does not contain the expected text",
            html=None,
        )
    ]

    monkeypatch.setattr(MailClient, "get_messages", lambda self: messages)

    client = MailClient(
        host="imap.example.com",
        email="user@example.com",
        password="password",
    )

    with pytest.raises(MessageNotFoundError):
        client.find_message(
            subject="Verify Your Email",
            body_pattern="please confirm",
        )


class FakeMailbox:
    def __init__(self) -> None:
        self.login_args = None
        self.deleted_uids = None
        self.expunge_called = False

    def login(self, email, password, folder):
        self.login_args = (email, password, folder)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def delete(self, uids):
        self.deleted_uids = uids

    def expunge(self):
        self.expunge_called = True


def test_delete_message_calls_delete_and_expunge(monkeypatch):
    fake_mailbox = FakeMailbox()

    monkeypatch.setattr("mail.mail_client.MailBox", lambda host, port=993: fake_mailbox)

    client = MailClient(
        host="imap.example.com",
        email="user@example.com",
        password="password",
    )

    client.delete_message("123")

    assert fake_mailbox.login_args == ("user@example.com", "password", "INBOX")
    assert fake_mailbox.deleted_uids == ["123"]
    assert fake_mailbox.expunge_called is True


def test_get_message_link_raises_when_verification_link_is_missing():
    message = MailMessage(
        uid="5",
        subject="Fw: Verify Your Email",
        sender="okvuaary9932338@outlook.com",
        date=None,
        body="Just a plain text message without a verification URL",
        html="<html><body>No verification link here</body></html>",
    )

    client = MailClient(
        host="imap.example.com",
        email="user@example.com",
        password="password",
    )

    with pytest.raises(VerificationLinkNotFoundError):
        client.get_message_link(message)
