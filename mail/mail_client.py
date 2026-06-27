import time
from datetime import datetime, timezone

from imap_tools import MailBox

from mail.exceptions import MessageNotFoundError, VerificationLinkNotFoundError
from mail.models import MailMessage
from mail.parsers import extract_password_recovery_link, extract_verification_link


class MailClient:
    def __init__(
        self,
        host: str,
        email: str,
        password: str,
        folder: str = "INBOX",
        port: int = 993,
    ) -> None:
        self.host = host
        self.email = email
        self.password = password
        self.folder = folder
        self.port = port

    def get_messages(self) -> list[MailMessage]:
        messages = []

        with MailBox(self.host, port=self.port).login(
            self.email,
            self.password,
            self.folder,
        ) as mailbox:
            for msg in mailbox.fetch():
                messages.append(MailMessage.from_imap_message(msg))

        return messages

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
        messages = self.get_messages()
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
        with MailBox(self.host, port=self.port).login(
            self.email,
            self.password,
            self.folder,
        ) as mailbox:
            mailbox.delete([uid])
            mailbox.expunge()
