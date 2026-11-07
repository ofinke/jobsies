from __future__ import annotations

import imaplib
import re
import smtplib
from datetime import UTC, datetime, timedelta, tzinfo
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime

from loguru import logger
from pytz import timezone

from jobsies.schemas.config import MailConfig
from jobsies.schemas.mail import ReceivedMail, SendMail
from jobsies.settings import get_settings

from .config_service import get_config_by_name


class MailService:
    """
    Send email and load recent unread messages using a named configuration.

    Accepted incoming messages are marked as read so subsequent loads skip them.
    """

    def __init__(self, configuration_name: str) -> None:
        """Load the named configuration used for IMAP retrieval and SMTP sending."""
        config = get_config_by_name(configuration_name)
        if not isinstance(config, MailConfig):
            msg = f"Configuration '{configuration_name}' must use the MailConfig model"
            logger.error(msg)
            raise TypeError(msg)
        self.config = config

    def load(self) -> list[ReceivedMail]:
        """
        Load recent unread emails matching the sender filter and mark them as read.

        Read messages are excluded from subsequent loads, even while they remain within
        the configured lookup period.
        """
        # Calculate the cutoff in the configured timezone and normalize sender addresses for matching.
        local_timezone = timezone(get_settings().tz_info)
        now = datetime.now(local_timezone)
        cutoff = (now.astimezone(UTC) - self.config.lookup_period).astimezone(local_timezone)
        senders = {sender.strip().casefold() for sender in self.config.senders}
        received_emails: list[ReceivedMail] = []

        try:
            # Search a day early because IMAP search has date-only precision; the cutoff is checked below.
            with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as client:
                client.login(self.config.username, self.config.password.get_secret_value())
                status, _ = client.select(self.config.mailbox, readonly=False)
                if status != "OK":
                    msg = f"Could not select IMAP mailbox '{self.config.mailbox}'"
                    logger.error(msg)
                    raise RuntimeError(msg)

                search_date = (cutoff - timedelta(days=1)).strftime("%d-%b-%Y")
                status, search_result = client.uid("search", None, "SINCE", search_date, "UNSEEN")
                if status != "OK":
                    msg = f"Could not search IMAP mailbox '{self.config.mailbox}'"
                    logger.error(msg)
                    raise RuntimeError(msg)
                if not search_result:
                    return received_emails

                # Fetch each candidate and keep only messages that pass parsing and configured filters.
                for uid in search_result[0].split():
                    status, fetch_result = client.uid("fetch", uid, "(RFC822 INTERNALDATE)")
                    if status != "OK" or not fetch_result:
                        logger.warning(f"Could not fetch IMAP message UID {uid!r}")
                        continue
                    logger.debug(f"Cleaning message {uid=}")
                    message = self._clean_message_data(
                        uid=uid,
                        fetch_result=fetch_result,
                        cutoff=cutoff,
                        senders=senders,
                        local_timezone=local_timezone,
                    )
                    if message is not None:
                        received_emails.append(message)
                        status, _ = client.uid("store", uid, "+FLAGS.SILENT", r"(\Seen)")
                        if status != "OK":
                            logger.warning(f"Could not mark IMAP message UID {uid!r} as seen")

        except (imaplib.IMAP4.error, OSError):
            logger.exception("Failed to load emails from the configured IMAP mailbox")
            raise

        return received_emails

    @staticmethod
    def _clean_message_data(
        uid: bytes,
        fetch_result: list[bytes | tuple[bytes, bytes | None]],
        cutoff: datetime,
        senders: set[str],
        local_timezone: tzinfo,
    ) -> ReceivedMail | None:
        """Parse a fetched message and return it only if it passes time and sender filters."""
        # Extract the message bytes and IMAP receive timestamp from the FETCH response.
        fetch_data = b" ".join(
            item[0] if isinstance(item, tuple) else item
            for item in fetch_result
            if (isinstance(item, tuple) and isinstance(item[0], bytes)) or isinstance(item, bytes)
        )
        raw_message = next(
            (item[1] for item in fetch_result if isinstance(item, tuple) and isinstance(item[1], bytes)),
            None,
        )
        internal_date = re.search(rb'INTERNALDATE "([^"]+)"', fetch_data)
        if raw_message is None or internal_date is None:
            return None

        try:
            received_at = parsedate_to_datetime(internal_date.group(1).decode())
        except (UnicodeDecodeError, TypeError, ValueError):
            return None

        # Normalize the receive time to UTC and discard messages older than the lookup period.
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=UTC)
        received_at = received_at.astimezone(local_timezone)
        if received_at < cutoff:
            return None
        message = BytesParser(policy=policy.default).parsebytes(raw_message)

        # Extract the sender and apply the allowlist unless the wildcard accepts all senders.
        sender_headers = message.get_all("From", [])
        sender_addresses = [address for _, address in getaddresses(sender_headers) if address]
        if not sender_addresses:
            return None
        sender_address = sender_addresses[0]
        if "*" not in senders and sender_address.casefold() not in senders:
            return None

        # Prefer a plain-text body, falling back to HTML, then return the normalized message model.
        body_part = message.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content() if body_part else ""
        if not isinstance(body, str):
            body = str(body)

        return ReceivedMail(
            uid=uid.decode(),
            sender=sender_address,
            subject=str(message["Subject"]) if message["Subject"] is not None else None,
            received_at=received_at,
            body=body,
            message_id=str(message["Message-ID"]) if message["Message-ID"] is not None else None,
        )

    def send(self, message: SendMail) -> None:
        """Send one email through the configured SMTP server using implicit TLS."""
        email_message = EmailMessage()
        email_message["From"] = message.sender
        email_message["To"] = ", ".join(message.recipients)
        email_message["Subject"] = message.subject
        email_message.set_content(message.body)

        with smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port) as client:
            client.login(self.config.username, self.config.password.get_secret_value())
            client.send_message(email_message)
