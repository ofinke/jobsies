import html
import re
from dataclasses import asdict

from fast_flights import FlightQuery, Passengers, Query, ResultList, create_query, get_flights
from fast_flights.parser import parse
from loguru import logger
from primp import Client

from jobsies.schemas.jobs import FlightPriceJobsieInput, FlightPriceJobsieOutput

from .base import BaseJobsie

CONSENT_FORM_INDEX = 1
MIN_CONSENT_FORMS = 2


class FlightPriceJobsie(BaseJobsie):
    """Jobsie for retrieving flight prices using the fast_flight google flights scraper."""

    output_schema = FlightPriceJobsieOutput
    input_schema = FlightPriceJobsieInput

    def __init__(self, **kwargs: object) -> None:
        """Validate and store the complete fast-flights query configuration."""
        self.input = self.input_schema(**kwargs)

    @staticmethod
    def _get_flights_after_consent(query: Query) -> ResultList:
        """Fetch and parse Google Flights after accepting the consent form."""
        client = Client(
            impersonate="chrome_145",
            impersonate_os="macos",
            referer=True,
            cookie_store=True,
        )
        response = client.get("https://www.google.com/travel/flights", params=query.params())
        forms = re.findall(r'<form action="https://consent.google.com/save".*?</form>', response.text, re.DOTALL)

        if len(forms) < MIN_CONSENT_FORMS:
            msg = "Google Flights returned a consent page without a usable consent form"
            raise RuntimeError(msg)

        consent_data = {
            name: html.unescape(value)
            for name, value in re.findall(
                r'<input type="hidden" name="([^"]+)" value="([^"]*)"',
                forms[CONSENT_FORM_INDEX],
            )
        }
        consent_response = client.post("https://consent.google.com/save", data=consent_data)
        return parse(consent_response.text)

    def _get_flights(self, query: Query) -> ResultList:
        """Fetch flights and recover from Google returning its consent page."""
        try:
            result = get_flights(query)
        except AttributeError as error:
            if "NoneType" not in str(error) or "text" not in str(error):
                raise
            logger.warning("Google Flights returned a consent page; retrying after accepting consent")
            result = self._get_flights_after_consent(query)

        if not isinstance(result, ResultList):
            msg = "fast-flights returned an unsupported result type"
            raise TypeError(msg)
        return result

    def execute(self) -> FlightPriceJobsieOutput:
        """Retrieve flight prices for the configured routes and filters."""
        query_data = self.input.model_dump()
        flights = [FlightQuery(**flight) for flight in query_data.pop("flights")]

        passengers = query_data.pop("passengers")
        if passengers is not None:
            passengers = Passengers(**passengers)

        query = create_query(flights=flights, passengers=passengers, **query_data)
        result = self._get_flights(query)

        return self.output_schema(
            flights=[asdict(flight) for flight in result],
            metadata=asdict(result.metadata),
        )
