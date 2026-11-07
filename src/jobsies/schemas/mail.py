from datetime import datetime

from pydantic import BaseModel, Field


class ReceivedMail(BaseModel):
    """An email retrieved from a configured mailbox."""

    uid: str
    sender: str
    subject: str | None
    received_at: datetime
    body: str
    message_id: str | None


class SendMail(BaseModel):
    """An email to send through a configured mail service."""

    sender: str
    recipients: list[str] = Field(min_length=1)
    subject: str
    body: str
