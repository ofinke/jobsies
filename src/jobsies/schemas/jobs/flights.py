from typing import Literal

from pydantic import Field

from .base import BaseJobsieInput, BaseJobsieOutput


class FlightQueryInput(BaseJobsieInput):
    """Data model for a single flight leg query."""

    date: str
    from_airport: str = Field(min_length=3, max_length=3)
    to_airport: str = Field(min_length=3, max_length=3)
    max_stops: int | None = Field(default=None, ge=0)
    airlines: list[str] | None = None
    earliest_departure_hour: int | None = Field(default=None, ge=0, le=23)
    latest_departure_hour: int | None = Field(default=None, ge=0, le=23)
    earliest_arrival_hour: int | None = Field(default=None, ge=0, le=23)
    latest_arrival_hour: int | None = Field(default=None, ge=0, le=23)
    max_duration_minutes: int | None = Field(default=None, ge=0)
    connecting_airports: list[str] | None = None
    min_layover_minutes: int | None = Field(default=None, ge=0)
    max_layover_minutes: int | None = Field(default=None, ge=0)
    less_emissions_only: bool = False


class PassengersInput(BaseJobsieInput):
    """Data model for passenger counts used in a flight query."""

    adults: int = Field(default=0, ge=0)
    children: int = Field(default=0, ge=0)
    infants_in_seat: int = Field(default=0, ge=0)
    infants_on_lap: int = Field(default=0, ge=0)


class FlightPriceJobsieInput(BaseJobsieInput):
    """Data model for the complete fast-flights query."""

    flights: list[FlightQueryInput] = Field(min_length=1)
    seat: Literal["economy", "premium-economy", "business", "first"] = "economy"
    trip: Literal["round-trip", "one-way", "multi-city"] = "one-way"
    passengers: PassengersInput | None = None
    language: str = ""
    currency: str = ""
    max_stops: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    carry_on_bags: int = Field(default=0, ge=0)
    checked_bags: int = Field(default=0, ge=0)
    hide_separate_and_self_transfer: bool = False
    exclude_basic_economy: bool = False


class AirlineOutput(BaseJobsieOutput):
    """Airline metadata returned by fast-flights."""

    code: str
    name: str


class AllianceOutput(BaseJobsieOutput):
    """Alliance metadata returned by fast-flights."""

    code: str
    name: str


class FlightMetadataOutput(BaseJobsieOutput):
    """Airline and alliance metadata returned with the search results."""

    airlines: list[AirlineOutput]
    alliances: list[AllianceOutput]


class AirportOutput(BaseJobsieOutput):
    """Airport information for a flight segment."""

    name: str
    code: str


class SimpleDatetimeOutput(BaseJobsieOutput):
    """Local date and time returned for a flight segment."""

    date: tuple[int, int, int]
    time: tuple[int, int]


class SingleFlightOutput(BaseJobsieOutput):
    """One non-stop segment within a returned itinerary."""

    from_airport: AirportOutput
    to_airport: AirportOutput
    departure: SimpleDatetimeOutput
    arrival: SimpleDatetimeOutput
    duration: int
    plane_type: str


class CarbonEmissionOutput(BaseJobsieOutput):
    """Carbon emissions for a returned itinerary, in grams."""

    typical_on_route: int
    emission: int


class FlightsOutput(BaseJobsieOutput):
    """One returned flight itinerary."""

    type: str
    price: int
    airlines: list[str]
    flights: list[SingleFlightOutput]
    carbon: CarbonEmissionOutput


class FlightPriceJobsieOutput(BaseJobsieOutput):
    """Data model for the output of FlightPriceJobsie."""

    flights: list[FlightsOutput]
    metadata: FlightMetadataOutput
