import base64
import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

from jobsies.services.redis import RedisHandler


def _redis_message(jobsie_id: int, eta: str) -> bytes:
    body = base64.b64encode(json.dumps([[jobsie_id], {}, {}]).encode()).decode()
    return json.dumps(
        [
            {
                "body": body,
                "headers": {"task": "task.run_dynamic_jobsie", "eta": eta},
            },
            "",
            "celery",
        ]
    ).encode()


def test_get_scheduled_tasks_decodes_and_groups_unacked_messages() -> None:
    """Test that scheduled task messages are decoded into jobsie execution times."""
    redis_handler = RedisHandler.__new__(RedisHandler)
    redis_handler.client = MagicMock()
    redis_handler.client.hgetall.return_value = {
        b"first": _redis_message(42, "2026-09-18T12:00:00+00:00"),
        b"second": _redis_message(42, "2026-09-18T13:00:00+00:00"),
    }

    scheduled = redis_handler.get_scheduled_tasks()

    assert scheduled == {
        42: [
            datetime(2026, 9, 18, 12, tzinfo=UTC),
            datetime(2026, 9, 18, 13, tzinfo=UTC),
        ]
    }


def test_get_scheduled_tasks_applies_limit_before_decoding() -> None:
    """Test that only the requested number of unacked entries is inspected."""
    redis_handler = RedisHandler.__new__(RedisHandler)
    redis_handler.client = MagicMock()
    redis_handler.client.hgetall.return_value = {
        b"first": _redis_message(1, "2026-09-18T12:00:00+00:00"),
        b"second": _redis_message(2, "2026-09-18T13:00:00+00:00"),
    }

    scheduled = redis_handler.get_scheduled_tasks(limit=1)

    assert scheduled == {1: [datetime(2026, 9, 18, 12, tzinfo=UTC)]}
