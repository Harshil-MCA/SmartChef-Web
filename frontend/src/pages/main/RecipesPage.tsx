import { useEffect, useState, type FormEvent } from "react";
import { useLocation } from "react-router-dom";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { RecipeResult } from "../../components/ResultCards";

export function RecipesPage() {
  const location = useLocation();
  const [dishName, setDishName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [shoppingMessage, setShoppingMessage] = useState("");

  async function addRecipeIngredients() {
    const items = (response?.ingredients ?? []).map((item: any) => ({ name: String(item.name ?? item).trim(), quantity: String(item.quantity ?? ""), category: "Recipe", notes: response?.recipe_name ?? "" })).filter((item: any) => item.name);
    await Promise.all(items.map((item: any) => apiFetch("/shopping-items/", { method: "POST", body: JSON.stringify(item) })));
    setShoppingMessage("Recipe ingredients added to your shopping list.");
  }

  useEffect(() => {
    const incoming = (location.state as { ingredients?: string[] } | null)?.ingredients;
    if (Array.isArray(incoming) && incoming.length) {
      setIngredients(incoming.join(", "));
      setDishName("");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [location.state]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const values = ingredients.split(",").map((item) => item.trim()).filter(Boolean);
    if (!dishName.trim() && !values.length) return;
    setLoading(true); setError("");
    try {
      setResponse(await apiFetch("/recipes/generate/", { method: "POST", body: JSON.stringify({
        ...(dishName.trim() ? { dish_name: dishName.trim() } : {}),
        ...(values.length ? { ingredients: values } : {}),
      }) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recipe generation failed");
    } finally {
      setLoading(false);
    }
  }

  const selectedIngredients = ingredients.split(",").map((item) => item.trim()).filter(Boolean);
  return <Panel title="AI Generated Recipe" subtitle="Create a recipe from your ingredients or dish name.">
    {selectedIngredients.length ? <section className="result-card"><h2>Detected Ingredients</h2><div className="pill-row">{selectedIngredients.map((item) => <span className="pill pill--accent" key={item}>{item}</span>)}</div></section> : null}
    <form className="stack" onSubmit={handleSubmit}>
      <label className="field"><span>Dish name</span><input value={dishName} onChange={(event) => setDishName(event.target.value)} placeholder="Optional dish name" /></label>
      <label className="field"><span>Ingredients</span><textarea value={ingredients} onChange={(event) => setIngredients(event.target.value)} rows={3} placeholder="Enter ingredients separated by commas" /></label>
      <button className="button button--primary" type="submit" disabled={loading || (!dishName.trim() && !selectedIngredients.length)}>{loading ? "Generating..." : "Generate Recipe"}</button>
    </form>
    {error ? <p className="form-error">{error}</p> : null}
    {response ? <RecipeResult recipe={response} /> : null}
    {response ? <div className="result-action"><button className="button button--primary" type="button" onClick={() => void addRecipeIngredients()}>Add Ingredients to Shopping List</button>{shoppingMessage ? <p className="form-success">{shoppingMessage}</p> : null}</div> : null}
  </Panel>;
}
