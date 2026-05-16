"""IMAP + API helpers for forgot-password / password-recovery UI flow."""

import logging
import re
import time
from datetime import datetime

from api.api_manager import ApiManager
from mail.exceptions import MessageNotFoundError
from mail.mail_client import MailClient
from resources.mail_creds import MailCreds

logger = logging.getLogger(__name__)

_RESET_SUBJECT = "Reset Password"
_EMAIL_RATE_LIMIT_RE = re.compile(
    r"restricted in a period of\s+(?P<seconds>[\d.]+)\s+seconds", re.I
)


def send_reset_password_email_with_retries(
    api_manager: ApiManager,
    email: str,
    *,
    deadline_s: float = 180.0,
) -> None:
    """GET /auth/send-reset-password?email=… с ретраями на 403 rate limit."""
    deadline = time.time() + deadline_s
    last_send = None
    while time.time() < deadline:
        last_send = api_manager.auth_api.send_reset_pass(
            {"email": email}, expected_status=[200, 403]
        )
        if last_send.status_code == 200:
            return

        wait_s = 60.0
        try:
            err = last_send.json()
            description = str(err.get("description", ""))
            match = _EMAIL_RATE_LIMIT_RE.search(description)
            if match:
                wait_s = float(match.group("seconds"))
        except Exception:
            pass
        time.sleep(min(wait_s + 1.0, 65.0))

    assert last_send is not None
    assert last_send.status_code == 200, (
        "Reset password email could not be sent due to rate limiting."
    )


def wait_imap_reset_password_link(
    *,
    recipient_email: str,
    since: datetime,
    timeout_s: float = 180.0,
    poll_interval_s: float = 3.0,
) -> str:
    client = MailClient(
        host=MailCreds.HOST,
        email=MailCreds.EMAIL,
        password=MailCreds.PASSWORD,
        folder=MailCreds.FOLDER,
        port=MailCreds.PORT,
    )
    message = client.wait_for_message(
        subject=_RESET_SUBJECT,
        to_contains=recipient_email,
        since=since,
        timeout_s=timeout_s,
        poll_interval_s=poll_interval_s,
    )
    link = client.get_reset_password_link(message)
    client.delete_message(message.uid)
    return link


def wait_imap_reset_password_link_after_ui_send(
    api_manager: ApiManager,
    *,
    email: str,
    since: datetime,
    imap_first_timeout_s: float = 90.0,
    imap_after_resend_timeout_s: float = 180.0,
    poll_interval_s: float = 3.0,
) -> str:
    """После UI «Отправить»: IMAP; если письма нет — API send-reset и снова IMAP."""
    logger.info(
        "IMAP first (%.0fs): Reset Password for %s after UI send",
        imap_first_timeout_s,
        email,
    )
    try:
        link = wait_imap_reset_password_link(
            recipient_email=email,
            since=since,
            timeout_s=imap_first_timeout_s,
            poll_interval_s=poll_interval_s,
        )
        logger.info("Reset password email found in IMAP without extra API send")
        return link
    except MessageNotFoundError:
        logger.info(
            "No Reset Password in IMAP after %.0fs — API send-reset-password for %s",
            imap_first_timeout_s,
            email,
        )
        send_reset_password_email_with_retries(api_manager, email)
        return wait_imap_reset_password_link(
            recipient_email=email,
            since=since,
            timeout_s=imap_after_resend_timeout_s,
            poll_interval_s=poll_interval_s,
        )
