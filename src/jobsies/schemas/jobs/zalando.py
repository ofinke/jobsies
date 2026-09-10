from pydantic import ConfigDict, Field

from .base import BaseJobsieInput, BaseJobsieOutput


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


class ZalandoJobsieInput(BaseJobsieInput):
    """Data model for input for the Zalando Jobsie."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://www.zalando.cz/example",
                    "size": "M",
                }
            ]
        }
    )

    url: str
    size: str
