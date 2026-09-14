import functools
from typing import Any

import redis


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
        """Return status containing liveness, memory usage and number of tasks in queue."""
        try:
            alive = bool(self.client.ping())
        except redis.RedisError:
            return {"alive": False, "memory_usage": "Unavailable", "tasks_in_queue": 0}

        memory_info = self.client.info("memory")
        return {
            "alive": alive,
            "memory_usage": memory_info.get("used_memory_human", "Unavailable"),
            "tasks_in_queue": self.client.llen("celery"),
        }


@functools.cache
def get_redis_handler(url: str) -> RedisHandler:
    """Return the reusable Redis handler."""
    return RedisHandler(url)
