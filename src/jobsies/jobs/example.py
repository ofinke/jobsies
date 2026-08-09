import httpx
from justhtml import JustHTML

from .base import BaseJobsie


class ExampleJobsie(BaseJobsie):
    """An example jobsie calls example.com domain and returns status message and page content."""

    def execute(self) -> dict:
        """Retrieves status and content of example.com."""
        response = httpx.get("https://example.com/")
        return {
            "status_code": response.status_code,
            "content": JustHTML(response.text).to_text(),
        }


# TODO: update the return so it returns only the text of the page