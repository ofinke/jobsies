from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from jobsies.schemas.config import MailConfig
from jobsies.schemas.mail import ReceivedMail
from jobsies.services.mail import MailService


def _make_imap_response(uid: int, internal_date: str, raw_message: bytes) -> tuple[bytes, bytes]:
    """Build the metadata and message tuple returned by an IMAP FETCH response."""
    metadata = f'{uid} (UID {uid} INTERNALDATE "{internal_date}" RFC822 {{{len(raw_message)}}}'.encode()
    return metadata, raw_message


def _make_service(
    monkeypatch: pytest.MonkeyPatch,
    config: MailConfig,
    uid_responses: list[tuple[str, list[bytes | tuple[bytes, bytes]]]],
    timezone_name: str = "UTC",
) -> tuple[MailService, MagicMock]:
    """Create a mail service backed by a mocked standard-library IMAP client."""
    client = MagicMock()
    client.__enter__.return_value = client
    client.select.return_value = ("OK", [b"1"])
    client.uid.side_effect = uid_responses
    monkeypatch.setattr("jobsies.services.mail.get_config_by_name", lambda _name: config)
    monkeypatch.setattr("jobsies.services.mail.get_settings", lambda: SimpleNamespace(tz_info=timezone_name))
    monkeypatch.setattr("jobsies.services.mail.imaplib.IMAP4_SSL", lambda *_args: client)
    return MailService("mail-config"), client


def _raw_email(sender: str, subject: str, body: str, message_id: str) -> bytes:
    """Build a minimal RFC 5322 plain-text message for IMAP responses."""
    return (
        f"From: {sender}\r\n"
        f"Subject: {subject}\r\n"
        f"Message-ID: {message_id}\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        f"{body}\r\n"
    ).encode()


@freeze_time("2026-03-10 12:00:00")
def test_load_receives_converts_and_filters_emails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retrieve IMAP messages, convert matching recent messages, and filter the rest."""
    config = MailConfig(
        imap_host="imap.example.com",
        username="mail-user",
        password="mail-password",  # noqa: S106
        lookup_period=timedelta(hours=24),
        senders=["alerts@example.com"],
    )
    recent_email = _raw_email(
        "Alerts <alerts@example.com>",
        "Service alert",
        "The service needs attention.",
        "<alert-1@example.com>",
    )
    other_sender_email = _raw_email(
        "Other <other@example.com>",
        "Not allowed",
        "This message should be filtered.",
        "<other-1@example.com>",
    )
    old_email = _raw_email(
        "Alerts <alerts@example.com>",
        "Old alert",
        "This message is outside the lookup period.",
        "<alert-old@example.com>",
    )
    service, client = _make_service(
        monkeypatch,
        config,
        [
            ("OK", [b"11 12 13"]),
            ("OK", [_make_imap_response(11, "10-Mar-2026 11:00:00 +0000", recent_email)]),
            ("OK", [_make_imap_response(12, "10-Mar-2026 10:00:00 +0000", other_sender_email)]),
            ("OK", [_make_imap_response(13, "09-Mar-2026 10:00:00 +0000", old_email)]),
        ],
    )

    received = service.load()

    assert received == [
        ReceivedMail(
            uid="11",
            sender="alerts@example.com",
            subject="Service alert",
            received_at=datetime(2026, 3, 10, 11, tzinfo=UTC),
            body="The service needs attention.\r\n",
            message_id="<alert-1@example.com>",
        )
    ]
    client.login.assert_called_once_with("mail-user", "mail-password")
    client.select.assert_called_once_with("INBOX", readonly=True)
    assert client.uid.call_count == 4


@freeze_time("2026-03-10 12:00:00")
def test_load_wildcard_accepts_emails_from_any_sender(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accept messages from any address when the configured sender list contains '*'."""
    config = MailConfig(
        imap_host="imap.example.com",
        username="mail-user",
        password="mail-password",  # noqa: S106
        lookup_period=timedelta(hours=6),
        senders=["*"],
    )
    raw_message = _raw_email("Unknown <unknown@example.com>", "Hello", "Wildcard accepted.", "<wildcard@example.com>")
    service, _ = _make_service(
        monkeypatch,
        config,
        [
            ("OK", [b"21"]),
            ("OK", [_make_imap_response(21, "10-Mar-2026 11:30:00 +0000", raw_message)]),
        ],
        timezone_name="Asia/Tokyo",
    )

    received = service.load()

    assert len(received) == 1
    assert received[0].sender == "unknown@example.com"
    assert received[0].subject == "Hello"
    assert received[0].received_at.isoformat() == "2026-03-10T20:30:00+09:00"
