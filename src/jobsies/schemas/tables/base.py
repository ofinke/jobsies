from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, text
from sqlmodel import Field, SQLModel


class TableDefaultModel(SQLModel, table=False):
    """Default table with autoincrementing index and self-updating created_at, updated_at columns."""

    # Database default
    id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            primary_key=True,
            autoincrement=True,
        ),
    )
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=text("CURRENT_TIMESTAMP"),
        ),
    )
