from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


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
            "onupdate": lambda: datetime.now(UTC),
        },
    )
