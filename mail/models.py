from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MailMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uid: str
    subject: str | None
    sender: str | None
    recipients: str | None = None
    date: datetime | None
    body: str | None
    html: str | None = None

    @classmethod
    def from_imap_message(cls, message: Any) -> "MailMessage":
        recipients = getattr(message, "to", None) or getattr(message, "to_", None)
        if isinstance(recipients, (list, tuple)):
            # imap_tools may return list[str] or list[tuple[name, email]] depending on parsing
            parts: list[str] = []
            for item in recipients:
                if isinstance(item, (list, tuple)) and item:
                    parts.append(str(item[-1]))
                else:
                    parts.append(str(item))
            recipients = ", ".join(parts) if parts else None
        elif recipients is not None:
            recipients = str(recipients)

        return cls(
            uid=str(message.uid),
            subject=message.subject,
            sender=message.from_,
            recipients=recipients,
            date=message.date,
            body=message.text,
            html=message.html,
        )
