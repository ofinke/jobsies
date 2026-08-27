import redis

from jobsies.settings import get_settings


class RedisHandler:
    """
    Redis client for the application.

    Similar to DatabaseHandler, only single reusable client is used by the application.
    """

    def __new__(cls) -> redis.Redis:
        settings = get_settings()
        return redis.from_url(settings.redis_url)
