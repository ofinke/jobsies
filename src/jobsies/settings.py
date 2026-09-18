from functools import cache

import pytz
from dotenv import find_dotenv
from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environmental variables."""

    model_config = SettingsConfigDict(
        env_file=find_dotenv(usecwd=True),
        extra="ignore",
    )

    db_url: str = Field(
        default="sqlite:///data/jobsies.sqlite",
        description="URL for database, default points to the data folder",
    )
    broker_redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis used by the worker as a broker, default points to the redis created by docker compose",
    )
    redbeat_redis_url: str = Field(
        default="redis://redis:6379/1",
        description="Redis used by the redbeat scheduler",
    )
    tz_info: str = Field(
        default="UTC",
        description="Timezone definition",
    )

    @field_validator("tz_info")
    @classmethod
    def validate_tz_info(cls, v: str) -> str:
        if v not in pytz.all_timezones:
            msg = f"'{v}' is not a valid timezone"
            logger.error(msg)
            raise ValueError(msg)
        return v


@cache
def get_settings() -> Settings:
    """Retruns cached application settings."""
    return Settings()
