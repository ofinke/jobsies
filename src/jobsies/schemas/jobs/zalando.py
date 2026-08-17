from pydantic import Field

from .base import BaseJobsieOutput


class ZalandoJobsieOutput(BaseJobsieOutput):
    """Data model for output of ZalandoJobsie."""

    item_name: str = Field(
        description="Extracted name of the monitored item",
    )
    price_czk: float = Field(
        description="Current price in CZK",
    )
    stock: str = Field(
        description="Current stock as a string value literal, example: 'one'",
    )
