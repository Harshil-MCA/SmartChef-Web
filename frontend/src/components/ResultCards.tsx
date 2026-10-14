import type { ReactNode } from "react";

function value(record: Record<string, any>, ...keys: string[]) {
  const found = keys.find((key) => record[key] !== undefined && record[key] !== null && record[key] !== "");
  return found ? String(record[found]) : "—";
}

export function MetricGrid({ data }: { data: Record<string, any> }) {
  const labels = ["calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium", "potassium", "calcium", "iron", "vitamin_a", "vitamin_c"];
  const units: Record<string, string> = { calories: " kcal", protein: " g", carbs: " g", fat: " g", fiber: " g", sugar: " g", sodium: " mg", potassium: " mg", calcium: " mg", iron: " mg", vitamin_a: " mcg", vitamin_c: " mg" };
  const entries = labels.map((key) => [key, data[key] ?? data[key.replace("_", " ")]] as const).filter(([, item]) => item !== undefined && item !== null);
  return <div className="metric-grid">{entries.map(([key, item]) => <div className="metric-card" key={key}><span>{key.replaceAll("_", " ")}</span><strong>{String(item)}{units[key] ?? ""}</strong></div>)}</div>;
}

export function RecipeResult({ recipe }: { recipe: Record<string, any> }) {
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const steps = Array.isArray(recipe.steps) ? recipe.steps : [];
  const detected = Array.isArray(recipe.input_ingredients) ? recipe.input_ingredients : [];
  const tips = Array.isArray(recipe.tips) ? recipe.tips : [];
  return <div className="result-sections">
    {detected.length > 0 && <section className="result-card"><h2>Detected Ingredients</h2><div className="pill-row">{detected.map((item: any) => <span className="pill pill--accent" key={String(item)}>{String(item)}</span>)}</div></section>}
    <section className="result-card result-card--hero"><h2>{value(recipe, "recipe_name", "recipeName", "title")}</h2><p>{value(recipe, "description")}</p><div className="meta-row"><span>◷ {value(recipe, "cook_time", "cookTime")}</span><span>◉ {value(recipe, "difficulty")}</span><span>♜ {value(recipe, "servings", "serving_count")} servings</span></div></section>
    {ingredients.length > 0 && <section className="result-card"><h2>Ingredients</h2><ul className="ingredient-list">{ingredients.map((item: any, index: number) => <li key={index}>{typeof item === "string" ? item : `${value(item, "name", "ingredient")} ${value(item, "quantity", "amount")} ${value(item, "unit")}`}</li>)}</ul></section>}
    {steps.length > 0 && <section className="result-card"><h2>Steps</h2><ol className="steps-list">{steps.map((step: any, index: number) => <li key={index}><strong>{index + 1}.</strong><span>{String(step)}</span></li>)}</ol></section>}
    {recipe.nutrition && <section className="result-card"><h2>Nutrition</h2><MetricGrid data={recipe.nutrition} /></section>}
    {tips.length > 0 && <section className="result-card"><h2>Cooking Tips</h2><ul className="ingredient-list">{tips.map((tip: any, index: number) => <li key={index}>{String(tip)}</li>)}</ul></section>}
  </div>;
}

export function NutritionResult({ match }: { match: Record<string, any> }) {
  const nutrition = match.nutrition && typeof match.nutrition === "object" ? match.nutrition : match;
  const calories = Number(nutrition.calories ?? 0);
  const healthText = calories > 500 ? "Energy-dense serving; balance it with vegetables and complementary foods." : "Moderate nutrition value for this serving.";
  return <section className="result-card"><h2>{value(match, "name", "ingredient")}</h2><p className="muted">Nutrition analysis</p><MetricGrid data={nutrition} /><h3>Health Analysis</h3><p>{healthText}</p></section>;
}

export function DietResult({ result }: { result: Record<string, any> }) {
  const payload = result.result_payload && typeof result.result_payload === "object" ? result.result_payload : result;
  const mealKeys = ["breakfast", "lunch", "dinner", "snacks"];
  const meals = mealKeys.map((key) => ({ key, meal: payload[key] })).filter(({ meal }) => meal && typeof meal === "object");
  const summary = payload.summary && typeof payload.summary === "object" ? payload.summary : {};
  return <div className="result-sections"><section className="result-card result-card--hero"><h2>One-Day Nutrition Plan</h2><p>Goal: {value(result, "goal")} · Budget: Rs.{value(result, "daily_budget")}</p></section>{meals.map(({ key, meal }: any) => <section className="result-card meal-card" key={key}><div className="meal-heading"><h2>{key[0].toUpperCase() + key.slice(1)}</h2><span>Est. Rs.{value(meal, "cost", "estimated_cost")}</span></div><h3>{value(meal, "name", "recipe_name", "dish_name", "title")}</h3><p>{value(meal, "portion")}</p><p>{Array.isArray(meal.ingredients) ? meal.ingredients.join(", ") : value(meal, "ingredients")}</p><MetricGrid data={meal} /></section>)}<section className="result-card"><h2>Daily Summary</h2><MetricGrid data={{ calories: summary.totalCalories, protein: summary.totalProtein, carbs: summary.totalCarbs, fat: summary.totalFat, fiber: summary.totalFiber, sugar: summary.totalSugar, sodium: summary.totalSodium }} /><div className="result-item"><strong>Budget Used</strong><span>Rs. {value(summary, "budgetUsed")}</span></div><div className="result-item"><strong>Budget Remaining</strong><span>Rs. {value(summary, "budgetRemaining")}</span></div></section>{Array.isArray(payload.shopping_list) && payload.shopping_list.length ? <section className="result-card"><h2>Shopping List</h2><ul className="ingredient-list">{payload.shopping_list.map((item: any, index: number) => <li key={index}>{String(item)}</li>)}</ul></section> : null}</div>;
}

export function ButtonIcon({ children }: { children: ReactNode }) { return <span aria-hidden="true" className="button-icon">{children}</span>; }
