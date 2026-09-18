import base64
import functools
import json
from datetime import datetime
from typing import Any

import redis

from jobsies.config import get_config

config = get_config()


class RedisHandler:
    """
    Redis client for the application.

    Provides access to a Redis client backed by a connection pool.
    """

    def __init__(self, url: str) -> None:
        """Initialize the Redis client and its connection pool."""
        self.client = redis.from_url(url)

    def acquire_enqueue_lock(self, lock_key: str, lock_timeout: int) -> bool:
        """Attempt to acquire an enqueue lock for the specified timeout."""
        return bool(self.client.set(lock_key, "enqueued", nx=True, ex=lock_timeout))

    def client_status(self) -> dict[str, Any]:
        """Return Redis liveness and broker diagnostics."""
        try:
            alive = bool(self.client.ping())
        except redis.RedisError:
            return {
                "alive": False,
                "memory_usage": "Unavailable",
                "version": "Unavailable",
                "uptime": "Unavailable",
            }

        info = self.client.info()

        return {
            "alive": alive,
            "memory_usage": info.get("used_memory_human", "Unavailable"),
            "version": info.get("redis_version", "Unavailable"),
            "uptime": info.get("uptime_in_seconds", "Unavailable"),
        }

    def get_scheduled_tasks(self, limit: int | None = None) -> dict[int, list[datetime]]:
        """Return scheduled dynamic jobsies currently held by Celery."""
        scheduled_tasks: dict[int, list[datetime]] = {}

        for raw_entry in list(self.client.hgetall("unacked").values())[:limit]:
            try:
                message, _, _ = json.loads(raw_entry)
                body = base64.b64decode(message["body"])
                decoded_body = json.loads(body)
                jobsie_id = int(decoded_body[0][0])
                eta = datetime.fromisoformat(message["headers"]["eta"])
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError, base64.binascii.Error):
                continue

            scheduled_tasks.setdefault(jobsie_id, []).append(eta)

        return scheduled_tasks

@functools.cache
def get_redis_handler(url: str) -> RedisHandler:
    """Return the reusable Redis handler."""
    return RedisHandler(url)
