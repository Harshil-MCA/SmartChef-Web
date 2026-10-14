import { useState, type FormEvent } from "react";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { DietResult } from "../../components/ResultCards";

export function DietPlannerPage() {
  const [age, setAge] = useState("");
  const [weight, setWeight] = useState("");
  const [height, setHeight] = useState("");
  const [budget, setBudget] = useState("");
  const [goal, setGoal] = useState("Weight Loss");
  const [customGoal, setCustomGoal] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [shoppingMessage, setShoppingMessage] = useState("");

  async function addPlanToShoppingList() {
    const payload = response?.result_payload && typeof response.result_payload === "object" ? response.result_payload : response;
    const items = Array.isArray(payload?.shopping_list) ? payload.shopping_list : [];
    await Promise.all(items.map((item: unknown) => apiFetch("/shopping-items/", { method: "POST", body: JSON.stringify({ name: String(item), category: "Diet plan", notes: "Generated diet plan" }) })));
    setShoppingMessage("Diet plan ingredients added to your shopping list.");
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      setResponse(await apiFetch("/diet-plans/generate/", { method: "POST", body: JSON.stringify({
        age: Number(age), weight: Number(weight), height: Number(height), daily_budget: Number(budget), goal: customGoal.trim() || goal,
      }) }));
    } catch (err) { setError(err instanceof Error ? err.message : "Diet plan generation failed"); }
    finally { setLoading(false); }
  }

  return <Panel title="SmartChef AI Diet Planner" subtitle="Create a clean budget-aware daily nutrition plan.">
    <section className="planner-card">
      <div className="planner-card__header"><h2>Create Your Daily Plan</h2><p>Enter age, weight, height, budget, and goal for a personalized plan.</p></div>
      <form className="stack" onSubmit={handleSubmit}>
        <label className="planner-field"><span>♟</span><input value={age} onChange={(event) => setAge(event.target.value)} type="number" min="1" max="120" placeholder="Age" required /></label>
        <label className="planner-field"><span>⚖</span><input value={weight} onChange={(event) => setWeight(event.target.value)} type="number" min="1" placeholder="Weight (kg)" required /></label>
        <label className="planner-field"><span>↕</span><input value={height} onChange={(event) => setHeight(event.target.value)} type="number" min="1" placeholder="Height (cm)" required /></label>
        <label className="planner-field"><span>₹</span><input value={budget} onChange={(event) => setBudget(event.target.value)} type="number" min="0" placeholder="Daily Budget (INR)" required /></label>
        <label className="planner-field planner-field--select"><span>◉</span><select value={goal} onChange={(event) => setGoal(event.target.value)}><option>Weight Loss</option><option>Weight Gain</option><option>Maintenance</option><option>Custom Goal</option></select></label>
        {goal === "Custom Goal" ? <label className="field"><span>Custom goal</span><input value={customGoal} onChange={(event) => setCustomGoal(event.target.value)} placeholder="Describe your goal" required /></label> : null}
        <button className="button button--primary planner-submit" type="submit" disabled={loading}>{loading ? "Generating..." : "🍴  Generate Diet Plan"}</button>
      </form>
    </section>
    {error ? <p className="form-error">{error}</p> : null}
    {response ? <DietResult result={response} /> : null}
    {response ? <div className="result-action"><button className="button button--primary" type="button" onClick={() => void addPlanToShoppingList()}>Add Plan to Shopping List</button>{shoppingMessage ? <p className="form-success">{shoppingMessage}</p> : null}</div> : null}
  </Panel>;
}
