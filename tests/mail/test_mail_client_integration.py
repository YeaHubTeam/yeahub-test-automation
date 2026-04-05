import os

import pytest

from mail.mail_client import MailClient
from resources.mail_creds import MailCreds


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MAIL_INTEGRATION") != "1",
    reason="Run with RUN_MAIL_INTEGRATION=1 to execute the live mail flow",
)


@pytest.mark.integration
def test_mail_flow_integration():
    client = MailClient(
        host=MailCreds.HOST,
        email=MailCreds.EMAIL,
        password=MailCreds.PASSWORD,
        folder=MailCreds.FOLDER,
        port=MailCreds.PORT,
    )

    found_message = client.find_message(subject="Verify Your Email")

    assert found_message is not None, "Verification email was not found"

    verification_link = client.get_message_link(found_message)

    assert verification_link is not None, "Verification link was not extracted"
    assert "verify-email" in verification_link

    uid = found_message.uid

    client.delete_message(uid)

    remaining_uids = {message.uid for message in client.get_messages()}

    assert uid not in remaining_uids
