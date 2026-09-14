import functools

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


@functools.cache
def get_redis_handler(url: str) -> RedisHandler:
    """Return the reusable Redis handler."""
    return RedisHandler(url)
