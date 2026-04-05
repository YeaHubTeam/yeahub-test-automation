from imap_tools import MailBox

from mail.parsers import extract_first_link


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

    def get_messages(self) -> list[dict]:
        messages = []

        with MailBox(self.host, port=self.port).login(
            self.email,
            self.password,
            self.folder,
        ) as mailbox:
            for msg in mailbox.fetch():
                messages.append(
                    {
                        "uid": msg.uid,
                        "subject": msg.subject,
                        "sender": msg.from_,
                        "date": msg.date,
                        "body": msg.text or msg.html,
                        "html": msg.html,
                    }
                )

        return messages

    def find_message(
        self,
        subject: str | None = None,
        body_pattern: str | None = None,
    ):
        messages = self.get_messages()
        matched_messages = []

        for message in messages:
            subject_matches = subject is None or subject in (message["subject"] or "")
            body_matches = body_pattern is None or body_pattern in (message["body"] or "")

            if subject_matches and body_matches:
                matched_messages.append(message)

        if not matched_messages:
            return None

        return max(matched_messages, key=lambda message: message["date"])

    def get_message_link(self, message: dict) -> str | None:
        return extract_first_link(
            text=message.get("body"),
            html=message.get("html"),
        )

    def get_registration_link(
        self,
        subject: str | None = None,
        body_pattern: str | None = None,
    ) -> str | None:
        message = self.find_message(subject=subject, body_pattern=body_pattern)

        if not message:
            return None

        return self.get_message_link(message)

    def delete_message(self, uid: str) -> None:
        with MailBox(self.host, port=self.port).login(
            self.email,
            self.password,
            self.folder,
        ) as mailbox:
            mailbox.delete([uid])
            mailbox.expunge()
