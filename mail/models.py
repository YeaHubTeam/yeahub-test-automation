from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MailMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uid: str
    subject: str | None
    sender: str | None
    date: datetime | None
    body: str | None
    html: str | None = None

    @classmethod
    def from_imap_message(cls, message: Any) -> "MailMessage":
        return cls(
            uid=str(message.uid),
            subject=message.subject,
            sender=message.from_,
            date=message.date,
            body=message.text,
            html=message.html,
        )
