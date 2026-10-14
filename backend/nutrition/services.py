from __future__ import annotations

import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings


class NutritionService:
    def __init__(self) -> None:
        self._database = self._load_json(settings.NUTRITION_DATABASE_PATH)
        self._aliases = self._load_json(settings.NUTRITION_ALIASES_PATH)
        self._csv_database: dict[str, dict[str, Any]] | None = None

    def lookup(self, ingredient: str) -> dict[str, Any] | None:
        normalized = self._normalize(ingredient)
        if not normalized:
            return None

        key = self._aliases.get(normalized, normalized)
        result = self._database.get(key) or self._database.get(normalized)
        if result:
            return {"name": key, "nutrition": result, "source": "local_json"}

        csv_match = self._csv_lookup(key, normalized)
        if csv_match:
            return {"name": csv_match["name"], "nutrition": csv_match["nutrition"], "source": "local_csv"}

        usda_match = self._usda_lookup(key or normalized)
        if usda_match:
            return {"name": usda_match["name"], "nutrition": usda_match["nutrition"], "source": "usda"}

        return None

    def batch_lookup(self, ingredients: list[str]) -> list[dict[str, Any]]:
        results = []
        for ingredient in ingredients:
            lookup = self.lookup(ingredient)
            if lookup:
                results.append(lookup)
        return results

    def scale_nutrition(self, ingredient: str, grams: float) -> dict[str, Any] | None:
        lookup = self.lookup(ingredient)
        if not lookup:
            return None

        factor = grams / 100.0
        payload = {
            key: round(value * factor, 2)
            for key, value in lookup["nutrition"].items()
            if isinstance(value, (int, float))
        }
        payload["name"] = lookup["name"]
        payload["grams"] = grams
        payload["source"] = lookup.get("source", "unknown")
        return payload

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_json(path_value: str) -> dict[str, Any]:
        path = Path(path_value)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if isinstance(raw, dict):
            return {str(key).lower(): value for key, value in raw.items()}
        return {}

    def _csv_lookup(self, key: str, normalized: str) -> dict[str, Any] | None:
        if self._csv_database is None:
            self._csv_database = self._load_csv_database(Path(settings.NUTRITION_CSV_DIR))
        if not self._csv_database:
            return None

        candidate = self._csv_database.get(key) or self._csv_database.get(normalized)
        if candidate:
            return candidate

        # Single-word ingredient input must never match a prepared dish that
        # merely contains the word. Let the USDA lookup resolve the ingredient
        # when the local dataset has no exact record.
        if len(normalized.split()) == 1:
            return None

        best_key = None
        best_score = 0.0
        for candidate_key in self._csv_database:
            score = self._score_match(normalized, candidate_key)
            if score > best_score:
                best_score = score
                best_key = candidate_key

        if best_key and best_score >= 0.72:
            return self._csv_database.get(best_key)
        return None

    def _load_csv_database(self, directory: Path) -> dict[str, dict[str, Any]]:
        database: dict[str, dict[str, Any]] = {}
        if not directory.exists():
            return database

        for csv_path in directory.rglob("*.csv"):
            try:
                with csv_path.open("r", encoding="utf-8", errors="ignore") as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        food_name = self._first_non_empty(row, ["food", "name", "description", "food name"])
                        if not food_name:
                            continue
                        nutrition = self._nutrition_from_csv_row(row)
                        if not nutrition:
                            continue
                        normalized_name = self._normalize(food_name)
                        if normalized_name and normalized_name not in database:
                            database[normalized_name] = {"name": food_name, "nutrition": nutrition}
                        lowered = food_name.lower().strip()
                        if lowered and lowered not in database:
                            database[lowered] = {"name": food_name, "nutrition": nutrition}
            except OSError:
                continue
        return database

    def _nutrition_from_csv_row(self, row: dict[str, str]) -> dict[str, Any]:
        return {
            "calories": self._first_float(row, ["caloricvalue", "calories", "energy"]),
            "protein": self._first_float(row, ["protein"]),
            "fat": self._first_float(row, ["fat", "total fat"]),
            "carbs": self._first_float(row, ["carbohydrates", "carbs", "carbohydrate"]),
            "fiber": self._first_float(row, ["dietaryfiber", "fiber", "fibre"]),
            "sugar": self._first_float(row, ["sugars", "sugar"]),
            "sodium": self._first_float(row, ["sodium"]),
            "potassium": self._first_float(row, ["potassium"]),
            "calcium": self._first_float(row, ["calcium"]),
            "iron": self._first_float(row, ["iron"]),
            "vitaminA": self._first_float(row, ["vitamina", "vitamin a"]),
            "vitaminC": self._first_float(row, ["vitaminc", "vitamin c"]),
            "water": self._first_float(row, ["water"]),
            "nutritionDensity": self._first_float(row, ["nutritiondensity", "nutrition density"]),
        }

    def _usda_lookup(self, ingredient: str) -> dict[str, Any] | None:
        api_key = settings.USDA_API_KEY
        if not api_key:
            return None

        query = urllib.parse.urlencode(
            {
                "api_key": api_key,
                "query": ingredient,
                "pageSize": 10,
                "requireAllWords": "true",
            }
        )
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?{query}"
        request = urllib.request.Request(url, method="GET")

        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
            return None

        foods = payload.get("foods")
        if not isinstance(foods, list) or not foods:
            return None

        best = self._best_food_match(foods, ingredient)
        if not best:
            return None

        nutrients = self._nutrition_from_usda_food(best)
        if not nutrients:
            return None

        return {"name": best.get("description") or ingredient, "nutrition": nutrients}

    def _nutrition_from_usda_food(self, food: dict[str, Any]) -> dict[str, Any] | None:
        nutrients_list = food.get("foodNutrients") or []
        nutrition = {
            "calories": self._nutrient_value(nutrients_list, ["energy"], convert_kj_to_kcal=True),
            "protein": self._nutrient_value(nutrients_list, ["protein"]),
            "fat": self._nutrient_value(nutrients_list, ["total lipid", "fat"]),
            "carbs": self._nutrient_value(nutrients_list, ["carbohydrate", "carbohydrates"]),
            "fiber": self._nutrient_value(nutrients_list, ["fiber", "fibre", "dietary fiber"]),
            "sugar": self._nutrient_value(nutrients_list, ["sugars", "sugar"]),
            "sodium": self._nutrient_value(nutrients_list, ["sodium"]),
            "potassium": self._nutrient_value(nutrients_list, ["potassium"]),
            "calcium": self._nutrient_value(nutrients_list, ["calcium"]),
            "iron": self._nutrient_value(nutrients_list, ["iron"]),
            "vitaminA": self._nutrient_value(nutrients_list, ["vitamin a"]),
            "vitaminC": self._nutrient_value(nutrients_list, ["vitamin c"]),
            "water": self._nutrient_value(nutrients_list, ["water"]),
            "nutritionDensity": None,
        }
        if not any(value is not None for value in nutrition.values()):
            return None
        return nutrition

    def _best_food_match(self, foods: list[Any], ingredient: str) -> dict[str, Any] | None:
        normalized = self._normalize(ingredient)
        best_food = None
        best_score = 0.0
        for item in foods:
            if not isinstance(item, dict):
                continue
            description = self._normalize(str(item.get("description", "")))
            if not description:
                continue
            score = self._score_match(normalized, description)
            if score > best_score:
                best_score = score
                best_food = item
        return best_food if best_score >= 0.68 else None

    def _nutrient_value(self, nutrients_list: list[Any], name_hints: list[str], *, convert_kj_to_kcal: bool = False) -> float | None:
        hints = [self._normalize(hint) for hint in name_hints]
        for item in nutrients_list:
            if not isinstance(item, dict):
                continue
            nutrient = item.get("nutrient") if isinstance(item.get("nutrient"), dict) else {}
            nutrient_name = self._normalize(
                str(
                    nutrient.get("name")
                    or item.get("nutrientName")
                    or item.get("name")
                    or ""
                )
            )
            unit_name = self._normalize(
                str(nutrient.get("unitName") or item.get("unitName") or item.get("unit") or "")
            )
            amount = self._as_float(item.get("amount") or item.get("value") or nutrient.get("amount") or nutrient.get("value"))
            if amount is None:
                continue
            if any(hint in nutrient_name for hint in hints):
                if convert_kj_to_kcal and "kj" in unit_name:
                    return round(amount / 4.184, 2)
                return round(amount, 2)
        return None

    def _first_float(self, row: dict[str, str], keys: list[str]) -> float | None:
        value = self._first_non_empty(row, keys)
        return self._as_float(value)

    def _first_non_empty(self, row: dict[str, str], keys: list[str]) -> str:
        normalized_row = {self._normalize(key): value for key, value in row.items()}
        for key in keys:
            value = normalized_row.get(self._normalize(key))
            if value and str(value).strip():
                return str(value).strip()
        return ""

    def _as_float(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            parsed = float(value)
            return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else None
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = float(text.replace(",", "."))
        except ValueError:
            return None
        return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else None

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value.lower())).strip()

    def _score_match(self, input_value: str, candidate: str) -> float:
        if input_value == candidate:
            return 1.0
        if input_value in candidate or candidate in input_value:
            return 0.9
        distance = self._levenshtein(input_value, candidate)
        max_length = max(len(input_value), len(candidate))
        if not max_length:
            return 0.0
        return 1 - (distance / max_length)

    def _levenshtein(self, left: str, right: str) -> int:
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
