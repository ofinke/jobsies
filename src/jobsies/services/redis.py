import redis

from jobsies.settings import get_settings


class RedisService:
    """Extremely simple reusable Redis client connected to the application's Redis URL."""

    def __new__(cls) -> redis.Redis:
        settings = get_settings()
        return redis.from_url(settings.redis_url)
