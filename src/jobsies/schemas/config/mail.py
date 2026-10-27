from datetime import timedelta

from pydantic import Field

from .base import BaseConfig


class MailConfig(BaseConfig):
    """IMAP connection and message filtering configuration."""

    imap_host: str = Field(
        description="Hostname of the IMAP server.",
    )
    imap_port: int = Field(
        default=993,
        gt=0,
        le=65535,
        description="Port of the IMAP server using implicit TLS.",
    )
    username: str = Field(
        description="Username used to authenticate with the IMAP server.",
    )
    password: str = Field(
        description="Password used to authenticate with the IMAP server.",
    )
    mailbox: str = Field(
        default="INBOX",
        description="Mailbox to search for incoming messages.",
    )
    lookup_period: timedelta = Field(
        gt=timedelta(0),
        description=(
            "How far back to search for messages. JSON values use ISO 8601 durations, for example 'PT6H' for six hours."
        ),
    )
    senders: list[str] = Field(
        description="Allowed sender email addresses. Include '*' to accept messages from any sender.",
    )
