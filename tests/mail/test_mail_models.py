from datetime import datetime, timezone

import pytest

from mail.models import MailMessage


pytestmark = [pytest.mark.unit, pytest.mark.regression]


class FakeImapMessage:
    def __init__(self) -> None:
        self.uid = 42
        self.subject = "Verify Your Email"
        self.from_ = "yeahub@yeahub.ru"
        self.date = datetime(2026, 4, 5, 11, 54, 19, tzinfo=timezone.utc)
        self.text = "Plain text body"
        self.html = "<html><body>HTML body</body></html>"


def test_mail_message_from_imap_message_maps_all_fields():
    message = FakeImapMessage()

    mail_message = MailMessage.from_imap_message(message)

    assert mail_message.uid == "42"
    assert mail_message.subject == "Verify Your Email"
    assert mail_message.sender == "yeahub@yeahub.ru"
    assert mail_message.date == datetime(2026, 4, 5, 11, 54, 19, tzinfo=timezone.utc)
    assert mail_message.body == "Plain text body"
    assert mail_message.html == "<html><body>HTML body</body></html>"
