from datetime import datetime, timezone

from imap_tools import MailBox

from mail.exceptions import MessageNotFoundError, VerificationLinkNotFoundError
from mail.models import MailMessage
from mail.parsers import extract_verification_link


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

    def find_message(
        self,
        subject: str,
    ) -> MailMessage:
        messages = self.get_messages()
        matched_messages: list[MailMessage] = []

        for message in messages:
            subject_matches = subject in (message.subject or "")

            if subject_matches:
                matched_messages.append(message)

        if not matched_messages:
            raise MessageNotFoundError("No email message matched the provided subject filter.")

        return max(
            matched_messages,
            key=lambda message: message.date or datetime.min.replace(tzinfo=timezone.utc),
        )

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

    def delete_message(self, uid: str) -> None:
        with MailBox(self.host, port=self.port).login(
            self.email,
            self.password,
            self.folder,
        ) as mailbox:
            mailbox.delete([uid])
            mailbox.expunge()
