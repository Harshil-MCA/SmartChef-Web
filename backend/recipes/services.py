from __future__ import annotations

from collections import Counter
from typing import Any

from ai.services import GeminiService
from recipes.models import RecipeRecord


class RecipeGenerationService:
    def __init__(self) -> None:
        self.ai = GeminiService()

    def generate(self, *, user, ingredients=None, dish_name="", serving_count=2) -> RecipeRecord:
        ingredients = ingredients or []
        ai_payload = self._generate_with_ai(ingredients=ingredients, dish_name=dish_name, serving_count=serving_count)
        if ai_payload:
            return self._persist_from_ai(
                user=user,
                payload=ai_payload,
                input_ingredients=ingredients,
                dish_name=dish_name,
                serving_count=serving_count,
            )

        return self._generate_fallback(
            user=user,
            ingredients=ingredients,
            dish_name=dish_name,
            serving_count=serving_count,
        )

    def _generate_with_ai(self, *, ingredients: list[str], dish_name: str, serving_count: int) -> dict[str, Any] | None:
        if not self.ai.configured:
            return None

        ingredient_list = ", ".join(ingredients) if ingredients else "No fixed ingredients"
        prompt = f"""
You are SmartChef AI. Generate one practical home-cooking recipe.

User input:
- Dish name: {dish_name or "Any suitable recipe"}
- Ingredients: {ingredient_list}
- Servings: {serving_count}

Return only valid JSON with this structure:
{{
  "recipe_name": "string",
  "description": "string",
  "ingredients": [
    {{"name":"string","quantity":"string","unit":"string"}}
  ],
  "steps": ["string"],
  "cook_time": "string",
  "difficulty": "string",
  "servings": "string",
  "tips": ["string"],
  "estimated_cost": "string",
  "nutrition": {{
    "calories": 0,
    "protein": 0,
    "carbs": 0,
    "fat": 0,
    "fiber": 0,
    "sugar": 0,
    "sodium": 0
  }}
}}

Rules:
- Treat the supplied ingredients as the required core ingredients; include each one in the returned ingredients and use them in the steps.
- Do not replace or ignore supplied ingredients. Add only reasonable common pantry ingredients when needed.
- Make the recipe clearly related to the supplied ingredients, not a random dish.
- Use simple, practical ingredients.
- Keep steps short and clear.
- Do not include markdown fences.
- If cost is unknown, still return a reasonable estimate string in Indian rupees.
"""
        try:
            result = self.ai.generate_json(prompt=prompt)
        except Exception:
            return None
        if not result:
            try:
                result = self.ai.generate_json(
                    prompt=(
                        "Return only JSON. Create a practical recipe using every supplied ingredient: "
                        f"{ingredient_list}. Include recipe_name, description, ingredients as an array of strings, "
                        "steps as an array of strings, cook_time, difficulty, servings, tips as an array of strings, "
                        "estimated_cost, and nutrition with calories, protein, carbs, fat, fiber, sugar, sodium."
                    )
                )
            except Exception:
                return None
        return result

    def _persist_from_ai(
        self,
        *,
        user,
        payload: dict[str, Any],
        input_ingredients: list[str],
        dish_name: str,
        serving_count: int,
    ) -> RecipeRecord | None:
        ingredients = self._normalize_ingredients(payload.get("ingredients"))
        steps = self._normalize_strings(payload.get("steps"))
        tips = self._normalize_strings(payload.get("tips"))
        nutrition = payload.get("nutrition") if isinstance(payload.get("nutrition"), dict) else {}
        recipe_name = str(payload.get("recipe_name") or dish_name or "Chef Special").strip()
        if not recipe_name:
            recipe_name = "Chef Special"

        if not ingredients or not steps:
            return None

        return RecipeRecord.objects.create(
            user=user,
            recipe_name=recipe_name,
            description=str(payload.get("description") or "").strip(),
            ingredients=ingredients,
            steps=steps,
            nutrition={
                "calories": self._as_number(nutrition.get("calories")),
                "protein": self._as_number(nutrition.get("protein")),
                "carbs": self._as_number(nutrition.get("carbs")),
                "fat": self._as_number(nutrition.get("fat")),
                "fiber": self._as_number(nutrition.get("fiber")),
                "sugar": self._as_number(nutrition.get("sugar")),
                "sodium": self._as_number(nutrition.get("sodium")),
            },
            estimated_cost=str(payload.get("estimated_cost") or "N/A"),
            cook_time=str(payload.get("cook_time") or "25 mins"),
            difficulty=str(payload.get("difficulty") or "Medium"),
            servings=str(payload.get("servings") or serving_count),
            input_ingredients=input_ingredients,
            source="ai",
        )

    def _generate_fallback(self, *, user, ingredients: list[str], dish_name: str, serving_count: int) -> RecipeRecord:
        normalized = [item.strip().lower() for item in ingredients if item.strip()]
        counts = Counter(normalized)
        unique_ingredients = list(counts.keys())
        pantry = unique_ingredients[:6] or ["mixed vegetables", "spices", "oil"]
        recipe_name = self._title_case(dish_name or ", ".join(pantry) or "Chef Special")

        steps = (
            self._build_steps_for_dish(dish_name, pantry)
            if dish_name.strip()
            else self._build_steps_for_ingredients(pantry)
        )

        return RecipeRecord.objects.create(
            user=user,
            recipe_name=recipe_name,
            description=f"SmartChef fallback recipe generated from {dish_name or 'selected ingredients'}.",
            ingredients=[{"name": item, "quantity": "1", "unit": "portion"} for item in pantry],
            steps=steps,
            nutrition={
                "calories": 320 + 40 * len(pantry),
                "protein": 12 + 2 * len(pantry),
                "carbs": 30 + 4 * len(pantry),
                "fat": 9 + len(pantry),
            },
            estimated_cost=f"Rs {max(20, 18 * len(pantry))}",
            cook_time="25 mins",
            difficulty="Easy",
            servings=str(serving_count),
            input_ingredients=ingredients,
            source="fallback",
        )

    def _normalize_ingredients(self, raw: Any) -> list[dict[str, str]]:
        items = []
        if not isinstance(raw, list):
            return items
        for item in raw:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    items.append({"name": text, "quantity": "1", "unit": ""})
                continue
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            items.append(
                {
                    "name": name,
                    "quantity": str(item.get("quantity") or "1").strip(),
                    "unit": str(item.get("unit") or "").strip(),
                }
            )
        return items

    def _normalize_strings(self, raw: Any) -> list[str]:
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    def _as_number(self, value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None

    def _build_steps_for_dish(self, dish_name: str, ingredients: list[str]) -> list[str]:
        readable = self._title_case(dish_name)
        return [
            f"Prep the ingredients for {readable}: {', '.join(ingredients)}.",
            "Heat oil and saute aromatics until fragrant.",
            "Add the main ingredients and cook until tender.",
            "Season to taste, adjust texture, and serve warm.",
        ]

    def _build_steps_for_ingredients(self, ingredients: list[str]) -> list[str]:
        return [
            f"Prepare {', '.join(ingredients)}.",
            "Cook the base ingredients until softened.",
            "Mix in seasoning and finish the dish to taste.",
            "Serve immediately while warm.",
        ]

    def _title_case(self, value: str) -> str:
        return " ".join(part.capitalize() for part in value.strip().split())


def generate_recipe_record(*, user, ingredients=None, dish_name="", serving_count=2):
    return RecipeGenerationService().generate(
        user=user,
        ingredients=ingredients,
        dish_name=dish_name,
        serving_count=serving_count,
    )
