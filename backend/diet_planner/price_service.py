from __future__ import annotations

import re
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class FoodPriceQuote:
    commodity: str
    market: str
    arrival_date: str
    min_price: float
    max_price: float
    modal_price: float
    unit: str

    @property
    def unit_label(self) -> str:
        return self.unit or "Rs/quintal"

    @property
    def price_per_kg(self) -> float:
        unit = self.unit_label.lower()
        if "100 g" in unit or "100g" in unit:
            return self.modal_price * 10.0
        if "100 kg" in unit or "100kg" in unit or "quintal" in unit:
            return self.modal_price / 100.0
        if "kg" in unit or "/kg" in unit:
            return self.modal_price
        if "litre" in unit or "liter" in unit or "/l" in unit:
            return self.modal_price
        return self.modal_price / 100.0

    def cost_for_grams(self, grams: float) -> float:
        unit = self.unit_label.lower()
        if "100 g" in unit or "100g" in unit:
            return self.modal_price * (grams / 100.0)
        if "100 kg" in unit or "100kg" in unit or "quintal" in unit:
            return self.price_per_kg * (grams / 1000.0)
        if "kg" in unit or "/kg" in unit:
            return self.price_per_kg * (grams / 1000.0)
        if "litre" in unit or "liter" in unit or "/l" in unit:
            return self.modal_price * (grams / 1000.0)
        return self.price_per_kg * (grams / 1000.0)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "FoodPriceQuote":
        return cls(
            commodity=str(record.get("commodity") or "").strip(),
            market=str(record.get("market") or "").strip(),
            arrival_date=str(record.get("arrival_date") or "").strip(),
            min_price=_as_float(record.get("min_price")),
            max_price=_as_float(record.get("max_price")),
            modal_price=_as_float(record.get("modal_price")),
            unit=str(record.get("unit") or record.get("price_unit") or "Rs/quintal").strip(),
        )


class FoodPriceService:
    _resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
    _timeout_seconds = 8

    _commodity_aliases = {
        "tomato": ["tomato"],
        "onion": ["onion", "onions"],
        "potato": ["potato", "potatoes"],
        "rice": ["rice", "paddy", "basmati rice"],
        "wheat": ["wheat", "wheat flour", "atta"],
        "moong": ["moong", "green gram", "mung", "mung bean"],
        "green gram": ["moong", "green gram", "mung", "mung bean"],
        "chickpea": ["gram", "chana", "chickpea", "kabuli chana", "desi chana"],
        "chickpeas": ["gram", "chana", "chickpea", "kabuli chana", "desi chana"],
        "bell pepper": ["bell pepper", "capsicum", "paprika", "sweet pepper"],
        "eggplant": ["eggplant", "brinjal", "aubergine"],
        "carrot": ["carrot"],
        "garlic": ["garlic"],
        "ginger": ["ginger"],
    }

    def __init__(self) -> None:
        self._cache: dict[str, FoodPriceQuote | None] = {}
        self._in_flight: dict[str, FoodPriceQuote | None] = {}

    @property
    def configured(self) -> bool:
        return bool(settings.DATA_GOV_IN_API_KEY)

    def estimate_cost(self, ingredients: list[str]) -> float | None:
        total_cost = 0.0
        priced_ingredients = 0

        for ingredient in ingredients:
            parsed = self._parse_ingredient_quantity(ingredient)
            if parsed is None:
                continue

            grams, commodity = parsed
            quote = self.get_current_price(commodity)
            if quote is None:
                continue

            total_cost += quote.cost_for_grams(grams)
            priced_ingredients += 1

        if priced_ingredients == 0 or total_cost <= 0:
            return None

        return round(total_cost, 2)

    def get_current_prices(self, commodities: list[str]) -> list[FoodPriceQuote]:
        unique: list[str] = []
        results: list[FoodPriceQuote] = []
        for commodity in commodities:
            normalized = self._normalize_commodity(commodity)
            if not normalized or normalized in unique:
                continue
            unique.append(normalized)
            quote = self.get_current_price(normalized)
            if quote is not None:
                results.append(quote)
        return results

    def get_current_price(self, commodity: str) -> FoodPriceQuote | None:
        normalized = self._normalize_commodity(commodity)
        if not normalized:
            return None

        if normalized in self._cache:
            return self._cache[normalized]

        if normalized in self._in_flight:
            return self._in_flight[normalized]

        quote = self._fetch_current_price(normalized)
        self._in_flight[normalized] = quote
        self._cache[normalized] = quote
        self._in_flight.pop(normalized, None)
        return quote

    def _fetch_current_price(self, commodity: str) -> FoodPriceQuote | None:
        api_key = settings.DATA_GOV_IN_API_KEY
        if not api_key:
            return None

        for lookup_term in self._lookup_terms_for_commodity(commodity):
            query = urllib.parse.urlencode(
                {
                    "api-key": api_key,
                    "format": "json",
                    "limit": 10,
                    "offset": 0,
                    "filters[commodity]": lookup_term,
                }
            )
            url = f"https://api.data.gov.in/resource/{self._resource_id}?{query}"
            request = urllib.request.Request(url, method="GET")

            try:
                with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                    payload = response.read().decode("utf-8")
            except (urllib.error.HTTPError, urllib.error.URLError):
                continue

            try:
                decoded = json.loads(payload)
            except ValueError:
                continue

            records = decoded.get("records")
            if not isinstance(records, list) or not records:
                continue

            best_record = self._best_matching_record(commodity, records)
            if not best_record:
                continue

            quote = FoodPriceQuote.from_record(best_record)
            if not quote.commodity or quote.modal_price <= 0:
                continue
            return quote

        return None

    def _lookup_terms_for_commodity(self, commodity: str) -> list[str]:
        normalized = self._normalize_commodity(commodity)
        terms = {normalized}
        for key, aliases in self._commodity_aliases.items():
            if normalized == key or normalized in aliases:
                terms.update(aliases)
        return [term for term in terms if term]

    def _best_matching_record(self, commodity: str, records: list[Any]) -> dict[str, Any] | None:
        target = self._normalize_commodity(commodity)
        best_record: dict[str, Any] | None = None
        best_score = 0.0

        for record in records:
            if not isinstance(record, dict):
                continue
            candidate = self._normalize_commodity(str(record.get("commodity") or ""))
            if not candidate:
                continue
            score = self._score_commodity_match(target, candidate)
            if score > best_score:
                best_score = score
                best_record = record

        return best_record if best_score >= 0.72 else None

    def _score_commodity_match(self, input_value: str, candidate: str) -> float:
        if input_value == candidate:
            return 1.0
        if input_value in candidate or candidate in input_value:
            return 0.9

        distance = _levenshtein(input_value, candidate)
        max_length = max(len(input_value), len(candidate))
        if max_length == 0:
            return 0.0
        return 1 - (distance / max_length)

    def _normalize_commodity(self, input_value: str) -> str:
        cleaned = _normalize_text(input_value)
        if not cleaned:
            return ""

        stripped = self._strip_quantity_and_units(cleaned)
        for alias, canonical in self._commodity_aliases.items():
            if stripped == alias or stripped in canonical:
                return alias
        return stripped

    def _strip_quantity_and_units(self, text: str) -> str:
        return re.sub(
            r"\b(?:\d+(?:[./]\d+)?\s*)?(?:g|gram|grams|kg|kilogram|kilograms|ml|l|liter|litre|cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|oz|ounce|ounces|lb|lbs|pound|pounds|slice|slices|pinch|dash)\b",
            " ",
            text,
        ).replace("  ", " ").strip()

    def _parse_ingredient_quantity(self, text: str) -> tuple[float, str] | None:
        cleaned = _normalize_text(text)
        if not cleaned:
            return None

        match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*(kg|kgs|g|gm|gms|gram|grams|kilogram|kilograms|mg|milligram|milligrams|ml|milliliter|milliliters|millilitre|millilitres|l|liter|liters|litre|litres)\b",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match:
            value = _as_float(match.group(1))
            unit = match.group(2).lower()
            if value <= 0:
                return None
            return _unit_to_grams(value, unit), self._normalize_commodity(cleaned)

        commodity = self._normalize_commodity(cleaned)
        if not commodity:
            return None
        return self._default_grams_for_commodity(commodity), commodity

    def _default_grams_for_commodity(self, commodity: str) -> float:
        defaults = {
            "rice": 150.0,
            "dal": 100.0,
            "wheat": 100.0,
            "wheat flour": 100.0,
            "atta": 100.0,
            "milk": 250.0,
            "banana": 120.0,
            "apple": 150.0,
            "paneer": 100.0,
            "tomato": 50.0,
            "onion": 50.0,
            "potato": 100.0,
            "carrot": 50.0,
            "spinach": 50.0,
            "peas": 50.0,
            "chickpea": 100.0,
            "green gram": 100.0,
            "moong": 100.0,
            "bell pepper": 50.0,
            "eggplant": 100.0,
            "garlic": 10.0,
            "ginger": 10.0,
        }
        return defaults.get(commodity, 100.0)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value.lower())).strip()


def _unit_to_grams(value: float, unit: str) -> float:
    if unit.startswith("kg") or unit.startswith("kilogram"):
        return value * 1000.0
    if unit == "mg" or unit.startswith("milligram"):
        return value / 1000.0
    if unit == "l" or unit.startswith("liter") or unit.startswith("litre"):
        return value * 1000.0
    return value


def _as_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        parsed = float(value)
        return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else 0.0
    try:
        parsed = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else 0.0


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    current = [0] * (len(right) + 1)
    for i, left_char in enumerate(left):
        current[0] = i + 1
        for j, right_char in enumerate(right):
            cost = 0 if left_char == right_char else 1
            current[j + 1] = min(
                current[j] + 1,
                previous[j + 1] + 1,
                previous[j] + cost,
            )
        previous, current = current, previous
    return previous[-1]
