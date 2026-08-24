from datetime import UTC, datetime
from typing import Self

from pytz import timezone, utc
from sqlmodel import Field, SQLModel

from jobsies.settings import get_settings

settings = get_settings()


class TableDefaultModel(SQLModel, table=False):
    """Default table with autoincrementing index and self-updating created_at, updated_at columns."""

    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={
            "default": lambda: datetime.now(UTC),
            "onupdate": None,
        },
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={
            "default": lambda: datetime.now(UTC),
            "onupdate": None,
        },
    )

    def datetimes_to_local_tz(self) -> Self:
        """Convert all datetime fields in-place to the app timezone."""
        # I fucking hate timezones
        # App runs in your defined timezone, database stores values in UTC
        # This method replaces in place all datetime values into settings.tz_info timezone
        target_tz = timezone(settings.tz_info)
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                utc_value = utc.localize(value) if value.tzinfo is None else value
                setattr(self, field_name, utc_value.astimezone(target_tz).replace(tzinfo=None))
        return self
