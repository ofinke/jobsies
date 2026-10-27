from datetime import datetime

from pydantic import BaseModel


class ReceivedMail(BaseModel):
    """An email retrieved from a configured mailbox."""

    uid: str
    sender: str
    subject: str | None
    received_at: datetime
    body: str
    message_id: str | None
