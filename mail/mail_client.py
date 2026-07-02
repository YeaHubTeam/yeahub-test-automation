import time
from datetime import datetime, timezone

from imap_tools import A, MailBox

from mail.exceptions import MessageNotFoundError, VerificationLinkNotFoundError
from mail.models import MailMessage
from mail.parsers import extract_password_recovery_link, extract_verification_link

_DEFAULT_IMAP_TIMEOUT_S = 30.0
_FETCH_LIMIT = 50


class MailClient:
    def __init__(
        self,
        host: str,
        email: str,
        password: str,
        folder: str = "INBOX",
        port: int = 993,
        *,
        imap_timeout_s: float = _DEFAULT_IMAP_TIMEOUT_S,
    ) -> None:
        self.host = host
        self.email = email
        self.password = password
        self.folder = folder
        self.port = port
        self.imap_timeout_s = imap_timeout_s

    def _login_mailbox(self) -> MailBox:
        return MailBox(self.host, port=self.port, timeout=self.imap_timeout_s).login(
            self.email,
            self.password,
            self.folder,
        )

    def _fetch_messages(
        self,
        *,
        subject: str | None = None,
        since: datetime | None = None,
    ) -> list[MailMessage]:
        if subject:
            criteria = A(subject=subject)
            if since is not None:
                criteria = A(subject=subject, date_gte=self._normalize_utc(since).date())
        else:
            criteria = A(all=True)

        messages: list[MailMessage] = []
        with self._login_mailbox() as mailbox:
            for msg in mailbox.fetch(criteria, limit=_FETCH_LIMIT, reverse=True):
                messages.append(MailMessage.from_imap_message(msg))
        return messages

    def get_messages(self) -> list[MailMessage]:
        return self._fetch_messages()

    @staticmethod
    def _normalize_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _message_matches_filters(
        self,
        message: MailMessage,
        *,
        subject: str,
        to_contains: str | None,
        since: datetime | None,
        min_date: datetime | None,
    ) -> bool:
        if subject not in (message.subject or ""):
            return False
        if to_contains and to_contains not in (message.recipients or ""):
            return False
        if not message.date:
            return since is None and min_date is None
        msg_date = self._normalize_utc(message.date)
        if since is not None and msg_date < self._normalize_utc(since):
            return False
        if min_date is not None and msg_date < self._normalize_utc(min_date):
            return False
        return True

    def find_message(
        self,
        subject: str,
        *,
        to_contains: str | None = None,
        since: datetime | None = None,
        min_date: datetime | None = None,
    ) -> MailMessage:
        messages = self._fetch_messages(subject=subject, since=since)
        matched_messages: list[MailMessage] = []

        for message in messages:
            if self._message_matches_filters(
                message,
                subject=subject,
                to_contains=to_contains,
                since=since,
                min_date=min_date,
            ):
                matched_messages.append(message)

        if not matched_messages:
            raise MessageNotFoundError("No email message matched the provided subject filter.")

        return max(
            matched_messages,
            key=lambda message: message.date or datetime.min.replace(tzinfo=timezone.utc),
        )

    def wait_for_message(
        self,
        subject: str,
        *,
        to_contains: str | None = None,
        since: datetime | None = None,
        min_date: datetime | None = None,
        timeout_s: float = 180.0,
        poll_interval_s: float = 3.0,
    ) -> MailMessage:
        deadline = time.time() + timeout_s
        last_error: Exception | None = None

        while time.time() < deadline:
            try:
                return self.find_message(
                    subject=subject,
                    to_contains=to_contains,
                    since=since,
                    min_date=min_date,
                )
            except MessageNotFoundError as exc:
                last_error = exc
                time.sleep(poll_interval_s)

        raise MessageNotFoundError(
            f"Verification email was not found within {timeout_s:.0f}s."
        ) from last_error

    def get_message_link(self, message: MailMessage) -> str:
        verification_link = extract_verification_link(
            text=message.body,
            html=message.html,
        )

        if verification_link is None:
            raise VerificationLinkNotFoundError(
                "Verification link was not found in the email message."
            )

        return verification_link

    def get_reset_password_link(self, message: MailMessage) -> str:
        recovery_link = extract_password_recovery_link(
            text=message.body,
            html=message.html,
        )
        if recovery_link is None:
            raise VerificationLinkNotFoundError(
                "Password recovery link was not found in the email message."
            )
        return recovery_link

    def delete_message(self, uid: str) -> None:
        with self._login_mailbox() as mailbox:
            mailbox.delete([uid])
            mailbox.expunge()
