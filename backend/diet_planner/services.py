from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.services import GeminiService
from nutrition.services import NutritionService
from diet_planner.price_service import FoodPriceService


@dataclass
class MealPlanItem:
    name: str
    portion: str
    ingredients: list[str]
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    fiber: float | None = None
    sugar: float | None = None
    sodium: float | None = None
    cost: float | None = None


class DietPlannerService:
    def __init__(self) -> None:
        self.nutrition = NutritionService()
        self.ai = GeminiService()
        self.prices = FoodPriceService()

    def generate(self, *, age: int, weight: float, height: float, daily_budget: float, goal: str) -> dict[str, Any]:
        ai_payload = self._generate_with_ai(
            age=age,
            weight=weight,
            height=height,
            daily_budget=daily_budget,
            goal=goal,
        )
        if ai_payload:
            return ai_payload

        normalized_goal = goal.lower().strip()
        if "loss" in normalized_goal:
            meals = self._weight_loss_plan()
        elif "gain" in normalized_goal:
            meals = self._weight_gain_plan()
        else:
            meals = self._maintenance_plan()

        enriched = [self._enrich_meal(item) for item in meals]
        shopping_list = self._build_shopping_list(enriched)
        summary = self._build_summary(enriched, daily_budget)

        return {
            "inputs": {
                "age": age,
                "weight": weight,
                "height": height,
                "daily_budget": daily_budget,
                "goal": goal,
            },
            "breakfast": enriched[0].__dict__,
            "lunch": enriched[1].__dict__,
            "dinner": enriched[2].__dict__,
            "snacks": enriched[3].__dict__,
            "summary": summary,
            "shopping_list": shopping_list,
            "source": "fallback",
        }

    def _generate_with_ai(
        self,
        *,
        age: int,
        weight: float,
        height: float,
        daily_budget: float,
        goal: str,
    ) -> dict[str, Any] | None:
        if not self.ai.configured:
            return None

        prompt = f"""
You are SmartChef AI. Generate one practical one-day diet plan.

User inputs:
- Age: {age}
- Weight: {weight} kg
- Height: {height} cm
- Daily budget: Rs {daily_budget}
- Goal: {goal}

Return only valid JSON with this structure:
{{
  "inputs": {{"age": 0, "weight": 0, "height": 0, "daily_budget": 0, "goal": ""}},
  "breakfast": {{"name": "", "portion": "", "ingredients": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0, "cost": 0}},
  "lunch": {{...}},
  "dinner": {{...}},
  "snacks": {{...}},
  "summary": {{
    "totalCalories": 0,
    "totalProtein": 0,
    "totalCarbs": 0,
    "totalFat": 0,
    "totalFiber": 0,
    "totalSugar": 0,
    "totalSodium": 0,
    "budgetUsed": 0,
    "budgetRemaining": 0,
    "estimatedWeeklyCost": 0
  }},
  "shopping_list": []
}}

Rules:
- Use practical, affordable ingredients.
- Keep meals suitable for home cooking.
- Use strings for meal names and portions.
- Do not include markdown fences or explanatory text.
"""
        try:
            payload = self.ai.generate_json(prompt=prompt)
        except Exception:
            return None

        if not payload:
            try:
                payload = self.ai.generate_json(prompt=(
                    "Return only JSON for a one-day diet plan. User: "
                    f"age {age}, weight {weight} kg, height {height} cm, budget Rs {daily_budget}, goal {goal}. "
                    "Include breakfast, lunch, dinner, snacks objects with name, portion, ingredients array, "
                    "calories, protein, carbs, fat, fiber, sugar, sodium, cost; include summary and shopping_list array."
                ))
            except Exception:
                return None
            if not payload:
                return None

        normalized = self._normalize_ai_plan(payload, age=age, weight=weight, height=height, daily_budget=daily_budget, goal=goal)
        if not normalized:
            return None
        normalized["source"] = "ai"
        return normalized

    def _normalize_ai_plan(
        self,
        payload: dict[str, Any],
        *,
        age: int,
        weight: float,
        height: float,
        daily_budget: float,
        goal: str,
    ) -> dict[str, Any] | None:
        breakfast = self._meal_from_payload(payload.get("breakfast"))
        lunch = self._meal_from_payload(payload.get("lunch"))
        dinner = self._meal_from_payload(payload.get("dinner"))
        snacks = self._meal_from_payload(payload.get("snacks"))
        meals = [breakfast, lunch, dinner, snacks]
        if any(meal is None for meal in meals):
            return None

        shopping_list = self._string_list(payload.get("shopping_list"))
        if not shopping_list:
            shopping_list = self._build_shopping_list([meal for meal in meals if meal is not None])

        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        summary_payload = {
            "totalCalories": self._as_number(summary.get("totalCalories")),
            "totalProtein": self._as_number(summary.get("totalProtein")),
            "totalCarbs": self._as_number(summary.get("totalCarbs")),
            "totalFat": self._as_number(summary.get("totalFat")),
            "totalFiber": self._as_number(summary.get("totalFiber")),
            "totalSugar": self._as_number(summary.get("totalSugar")),
            "totalSodium": self._as_number(summary.get("totalSodium")),
            "budgetUsed": self._as_number(summary.get("budgetUsed")),
            "budgetRemaining": self._as_number(summary.get("budgetRemaining")),
            "estimatedWeeklyCost": self._as_number(summary.get("estimatedWeeklyCost")),
        }

        return {
            "inputs": {
                "age": age,
                "weight": weight,
                "height": height,
                "daily_budget": daily_budget,
                "goal": goal,
            },
            "breakfast": breakfast.__dict__,
            "lunch": lunch.__dict__,
            "dinner": dinner.__dict__,
            "snacks": snacks.__dict__,
            "summary": summary_payload,
            "shopping_list": shopping_list,
        }

    def _meal_from_payload(self, raw: Any) -> MealPlanItem | None:
        if not isinstance(raw, dict):
            return None
        ingredients = self._string_list(raw.get("ingredients"))
        if not ingredients:
            ingredients = self._infer_ingredients_from_text(f"{raw.get('name', '')} {raw.get('portion', '')}")
        return MealPlanItem(
            name=str(raw.get("name") or "").strip(),
            portion=str(raw.get("portion") or "").strip(),
            ingredients=ingredients,
            calories=self._as_number(raw.get("calories")),
            protein=self._as_number(raw.get("protein")),
            carbs=self._as_number(raw.get("carbs")),
            fat=self._as_number(raw.get("fat")),
            fiber=self._as_number(raw.get("fiber")),
            sugar=self._as_number(raw.get("sugar")),
            sodium=self._as_number(raw.get("sodium")),
            cost=self._as_number(raw.get("cost")),
        )

    def _weight_loss_plan(self) -> list[MealPlanItem]:
        return [
            MealPlanItem("Vegetable Oats Bowl", "1 bowl", ["oats", "milk", "spinach", "tomato"]),
            MealPlanItem("Dal Rice with Salad", "1 plate", ["rice", "dal", "onion", "tomato"]),
            MealPlanItem("Vegetable Soup", "1 bowl", ["carrot", "potato", "onion", "tomato"]),
            MealPlanItem("Roasted Chana", "1 handful", ["soy beans"]),
        ]

    def _maintenance_plan(self) -> list[MealPlanItem]:
        return [
            MealPlanItem("Oats with Banana", "1 bowl", ["oats", "banana", "milk", "peanuts"]),
            MealPlanItem("Rice, Dal and Veg Curry", "1 plate", ["rice", "dal", "tomato", "onion"]),
            MealPlanItem("Fruit Bowl", "1 cup", ["banana", "apple", "grapes"]),
            MealPlanItem("Roti with Paneer Bhurji", "2 rotis", ["wheat flour", "onion", "tomato", "paneer"]),
        ]

    def _weight_gain_plan(self) -> list[MealPlanItem]:
        return [
            MealPlanItem("Oats Banana Milk Bowl", "1 large bowl", ["oats", "milk", "banana", "peanuts"]),
            MealPlanItem("Rice, Dal and Tomato Bowl", "1 plate", ["rice", "dal", "tomato", "onion"]),
            MealPlanItem("Banana Peanuts Bowl", "1 bowl", ["banana", "peanuts", "milk"]),
            MealPlanItem("Roti with Chickpea Curry", "2 rotis", ["wheat flour", "chickpea", "onion", "tomato"]),
        ]

    def _enrich_meal(self, meal: MealPlanItem) -> MealPlanItem:
        nutrition_rows = [self.nutrition.lookup(item) for item in meal.ingredients]
        nutrition_rows = [row for row in nutrition_rows if row]
        calories = sum((row["nutrition"].get("calories") or 0) for row in nutrition_rows) or None
        protein = sum((row["nutrition"].get("protein") or 0) for row in nutrition_rows) or None
        carbs = sum((row["nutrition"].get("carbs") or 0) for row in nutrition_rows) or None
        fat = sum((row["nutrition"].get("fat") or 0) for row in nutrition_rows) or None
        fiber = sum((row["nutrition"].get("fiber") or 0) for row in nutrition_rows) or None
        sugar = sum((row["nutrition"].get("sugar") or 0) for row in nutrition_rows) or None
        sodium = sum((row["nutrition"].get("sodium") or 0) for row in nutrition_rows) or None
        cost = self._estimate_cost(meal.ingredients)
        return MealPlanItem(
            meal.name,
            meal.portion,
            meal.ingredients,
            calories=round(calories, 2) if calories is not None else None,
            protein=round(protein, 2) if protein is not None else None,
            carbs=round(carbs, 2) if carbs is not None else None,
            fat=round(fat, 2) if fat is not None else None,
            fiber=round(fiber, 2) if fiber is not None else None,
            sugar=round(sugar, 2) if sugar is not None else None,
            sodium=round(sodium, 2) if sodium is not None else None,
            cost=cost,
        )

    def _estimate_cost(self, ingredients: list[str]) -> float:
        live_cost = self.prices.estimate_cost(ingredients)
        if live_cost is not None:
            return live_cost

        price_table = {
            "banana": 12.0,
            "apple": 18.0,
            "oats": 20.0,
            "milk": 22.0,
            "rice": 10.0,
            "dal": 18.0,
            "tomato": 8.0,
            "onion": 6.0,
            "carrot": 10.0,
            "potato": 8.0,
            "spinach": 12.0,
            "peanuts": 16.0,
            "wheat flour": 12.0,
            "paneer": 38.0,
            "soy beans": 14.0,
            "chickpea": 15.0,
            "grapes": 20.0,
        }
        return round(sum(price_table.get(item, 10.0) for item in ingredients), 2)

    def _build_shopping_list(self, meals: list[MealPlanItem]) -> list[str]:
        items: list[str] = []
        for meal in meals:
            for ingredient in meal.ingredients:
                if ingredient not in items:
                    items.append(ingredient)
        return items

    def _build_summary(self, meals: list[MealPlanItem], daily_budget: float) -> dict[str, Any]:
        budget_used = sum(meal.cost or 0 for meal in meals)
        return {
            "totalCalories": sum(meal.calories or 0 for meal in meals) or None,
            "totalProtein": sum(meal.protein or 0 for meal in meals) or None,
            "totalCarbs": sum(meal.carbs or 0 for meal in meals) or None,
            "totalFat": sum(meal.fat or 0 for meal in meals) or None,
            "totalFiber": sum(meal.fiber or 0 for meal in meals) or None,
            "totalSugar": sum(meal.sugar or 0 for meal in meals) or None,
            "totalSodium": sum(meal.sodium or 0 for meal in meals) or None,
            "budgetUsed": round(budget_used, 2),
            "budgetRemaining": round(daily_budget - budget_used, 2),
            "estimatedWeeklyCost": round(budget_used * 7, 2),
        }

    def _string_list(self, raw: Any) -> list[str]:
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    def _as_number(self, raw: Any) -> float | None:
        if isinstance(raw, (int, float)):
            return float(raw)
        try:
            return float(str(raw))
        except (TypeError, ValueError):
            return None

    def _infer_ingredients_from_text(self, text: str) -> list[str]:
        cleaned = [part.strip().lower() for part in text.split() if part.strip()]
        return cleaned[:4]
