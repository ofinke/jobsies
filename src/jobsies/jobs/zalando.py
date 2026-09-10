import json
from typing import Any

import httpx2
from justhtml import JustHTML
from loguru import logger

from jobsies.schemas.jobs import ZalandoJobsieInput, ZalandoJobsieOutput

from .base import BaseJobsie

JSON_SCRIPT_TYPES = {
    "application/json",
    "application/ld+json",
    "application/geo+json",
}


class ZalandoJobsie(BaseJobsie):
    """Jobsie for retrieving current price and stock of an item from Zalando."""

    output_schema = ZalandoJobsieOutput
    input_schema = ZalandoJobsieInput

    def __init__(self, url: str, size: str) -> None:
        """
        Initialize jobsie with required parameters.

        Args:
            url: exact url of an item
            size: exact size name as mentioned on the Zalando page

        """
        self.input_schema(url=url, size=size)
        self.url = str(url)
        self.size = str(size)

    def _get_content_from_url(self) -> JustHTML:
        """Retrieves HTML content from URL."""
        # curl agent is allowed
        headers = {
            "User-Agent": "curl/8.11.1",
            "Accept": "*/*",
        }
        response = httpx2.get(self.url, headers=headers)
        response.raise_for_status()

        logger.debug(f"{self.url[:20]}... responded with {response.status_code}")

        return JustHTML(response.text, sanitize=False)

    @staticmethod
    def _script_source(script: Any) -> str:
        """Concatenates text from the script children."""
        return "".join(child.data for child in script.children or [] if child.name == "#text")

    @staticmethod
    def _embedded_json_values(source: str) -> list[object]:
        """Extracts embedded JSON values from the source text."""
        decoder = json.JSONDecoder()
        values: list[object] = []
        position = 0

        while position < len(source):
            next_object = source.find("{", position)
            next_array = source.find("[", position)
            candidates = [index for index in (next_object, next_array) if index >= 0]

            if not candidates:
                break

            start = min(candidates)
            try:
                value, end = decoder.raw_decode(source, start)
            except json.JSONDecodeError:
                position = start + 1
                continue

            values.append(value)
            position = end

        return values

    def _extract_jsons_from_html(self, content: JustHTML) -> list[dict[str, object]]:
        """Extracts all viable jsons/dictionaries from URL content."""
        results: list[dict[str, object]] = []

        for script in content.query("script"):
            source = self._script_source(script).strip()
            if not source:
                continue

            attrs = script.attrs or {}
            script_type = attrs.get("type", "").lower()

            if script_type in JSON_SCRIPT_TYPES:
                try:
                    results.append(json.loads(source))
                except json.JSONDecodeError as error:
                    logger.warning(f"Failed to decode JSON script: {error}")
                continue

            results.extend(self._embedded_json_values(source))

        return results

    @staticmethod
    def _extract_simpleswithstock(data: list[dict[str, object]]) -> list[dict[str, object]]:
        """Selects only jsons which start with key "simplesWithStock"."""
        results: list[dict[str, object]] = []

        for item in data:
            if not isinstance(item, dict):
                continue
            simples = item.get("simplesWithStock")
            if isinstance(simples, list):
                results.extend(sub for sub in simples if isinstance(sub, dict))
            results.extend(ZalandoJobsie._extract_simpleswithstock([v for v in item.values() if isinstance(v, dict)]))
            results.extend(
                ZalandoJobsie._extract_simpleswithstock(
                    [v for v in item.values() if isinstance(v, list) and all(isinstance(x, dict) for x in v)]
                )
            )

        return results

    def _extract_size(self, data: list[dict[str, object]]) -> list[dict[str, object]]:
        """Selects only dicts that contain key-value pair "size" matching given size."""
        results: list[dict[str, object]] = []

        for item in data:
            if not isinstance(item, dict):
                continue
            if "size" in item and item["size"] == self.size:
                results.append(item)
            results.extend(ZalandoJobsie._extract_size([v for v in item.values() if isinstance(v, dict)], self.size))
            results.extend(
                ZalandoJobsie._extract_size(
                    [v for v in item.values() if isinstance(v, list) and all(isinstance(x, dict) for x in v)],
                    self.size,
                )
            )

        return results

    @staticmethod
    def _extract_item_name(content: JustHTML) -> str | None:
        """Extracts product name from og:title meta tag, stripped to just the brand and product name."""
        for meta in content.query('meta[property="og:title"]'):
            title = (meta.attrs or {}).get("content", "")
            if title:
                parts = title.split(" - ")
                return parts[0] if parts else title
        return None

    @staticmethod
    def _extract_price_amount(offer: dict) -> float | None:
        """Extracts current price in CZK from an offer dict, preferring promotional price over original."""
        price_data = offer.get("price")
        if not isinstance(price_data, dict):
            return None
        for key in ("promotional", "original"):
            amount = price_data.get(key)
            if isinstance(amount, dict) and "amount" in amount:
                return amount["amount"] / 100
        return None

    @staticmethod
    def _extract_stock_quantity(offer: dict) -> str | None:
        """Extracts stock quantity from an offer dict."""
        stock_data = offer.get("stock")
        if isinstance(stock_data, dict):
            return stock_data.get("quantity")
        return None

    @staticmethod
    def _extract_default_offer(offers: list) -> dict | None:
        """Extracts the default offer from allOffers list."""
        for offer in offers:
            if isinstance(offer, dict) and offer.get("isDefaultOffer"):
                return offer
        return None

    @staticmethod
    def _extract_single_offer(item: dict) -> dict | None:
        """Extracts single offer from an item dict."""
        offer = item.get("offer")
        if isinstance(offer, dict):
            return offer
        return None

    def _extract_price(self, data: list[dict[str, object]]) -> float | None:
        """Extracts current price in CZK for the configured size."""
        for item in data:
            if not isinstance(item, dict) or item.get("size") != self.size:
                continue

            offers = item.get("allOffers")
            if isinstance(offers, list):
                offer = self._extract_default_offer(offers)
                if offer is not None:
                    price = self._extract_price_amount(offer)
                    if price is not None:
                        return price

            offer = self._extract_single_offer(item)
            if offer is not None:
                price = self._extract_price_amount(offer)
                if price is not None:
                    return price

        return None

    def _extract_stock(self, data: list[dict[str, object]]) -> str | None:
        """Extracts stock quantity for the configured size."""
        for item in data:
            if not isinstance(item, dict) or item.get("size") != self.size:
                continue

            offers = item.get("allOffers")
            if isinstance(offers, list):
                offer = self._extract_default_offer(offers)
                if offer is not None:
                    stock = self._extract_stock_quantity(offer)
                    if stock is not None:
                        return stock

            offer = self._extract_single_offer(item)
            if offer is not None:
                stock = self._extract_stock_quantity(offer)
                if stock is not None:
                    return stock

        return None

    def execute(self) -> ZalandoJobsieOutput:
        """Retrieves status and content of example.com."""
        # Retrieve content from the URL
        content = self._get_content_from_url()

        # The HTML contains a lot of complex jsons, we go through them in sequence
        data = self._extract_jsons_from_html(content)
        logger.debug(f"Extracted {len(data)} JSONs from the raw html content.")
        data = self._extract_simpleswithstock(data)
        logger.debug(f"Extracted {len(data)} JSONs with 'simplesWithStock' key.")
        stock = self._extract_size(data)
        logger.debug(f"Extracted {len(stock)} JSONs with '{self.size}' size value.")

        # Extract final data we are interested in
        output = {
            "item_name": self._extract_item_name(content),
            "price_czk": self._extract_price(stock),
            "stock": self._extract_stock(stock),
        }
        logger.debug(f"Extracted price and stock: price_czk={output['price_czk']}, stock={output['stock']}")

        return self.output_schema(**output)
