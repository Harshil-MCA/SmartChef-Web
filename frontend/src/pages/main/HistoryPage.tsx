import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import { EmptyState } from "../../components/StateViews";
import { Panel } from "../../components/Panel";
import type { HistoryEntry } from "../../types";

export function HistoryPage() {
  const [items, setItems] = useState<HistoryEntry[]>([]); const [loading, setLoading] = useState(true); const [type, setType] = useState("all"); const [error, setError] = useState("");
  function renderDetails(item: HistoryEntry) {
    const payload = item.payload ?? {};
    if (item.entry_type === "ingredient") {
      const rows = Array.isArray(payload.items) ? payload.items as Array<{ name?: string; confidence?: number }> : [];
      const candidates = Array.isArray(payload.candidates) ? payload.candidates as Array<{ name?: string; confidence?: number }> : [];
      return <div className="history-details">{rows.map((row, i) => <div className="result-item" key={i}><strong>Ingredient</strong><span>{row.name ?? "Unknown"} {typeof row.confidence === "number" ? `— ${(row.confidence * 100).toFixed(2)}%` : ""}</span></div>)}{candidates.length ? <><strong>Detection details</strong>{candidates.map((row, i) => <div className="result-item" key={`${row.name}-${i}`}><span>{row.name ?? "Unknown"}</span><span>{typeof row.confidence === "number" ? `${(row.confidence * 100).toFixed(2)}%` : ""}</span></div>)}</> : null}</div>;
    }
    if (item.entry_type === "nutrition") { const match = Array.isArray(payload.matches) ? payload.matches[0] : undefined; const n = (payload.nutrition && typeof payload.nutrition === "object" ? payload.nutrition : match && typeof match === "object" ? match : payload) as Record<string, unknown>; const labels: Record<string, string> = { name: "Ingredient", grams: "Weight", calories: "Calories", protein: "Protein", carbs: "Carbohydrates", fat: "Fat", fiber: "Fiber", sugar: "Sugar" }; const keys = ["name", "grams", "calories", "protein", "carbs", "fat", "fiber", "sugar"]; return <div className="history-details">{keys.filter((key) => n[key] !== undefined && n[key] !== null).map((key) => <div className="result-item" key={key}><strong>{labels[key]}</strong><span>{String(n[key])}{key === "grams" ? " g" : key === "calories" ? " kcal" : ["protein", "carbs", "fat", "fiber", "sugar"].includes(key) ? " g" : ""}</span></div>)}</div>; }
    return <p className="muted">{item.summary || "Saved activity"}</p>;
  }
  useEffect(() => { async function load() { try { const data = await apiFetch<{ results?: HistoryEntry[] }>("/history/?page=1"); setItems(data.results ?? []); setError(""); } catch (err) { setError(err instanceof Error ? err.message : "Could not load history"); } finally { setLoading(false); } } void load(); const interval = window.setInterval(() => void load(), 20_000); return () => window.clearInterval(interval); }, []);
  const visible = items.filter((item) => type === "all" || item.entry_type === type);
  return <Panel title="History" subtitle="Your saved SmartChef activity."><div className="pill-row">{["all", "ingredient", "recipe", "nutrition", "diet"].map((value) => <button key={value} type="button" className={type === value ? "pill pill--accent" : "pill"} onClick={() => setType(value)}>{value[0].toUpperCase() + value.slice(1)}</button>)}</div>{loading ? <p className="muted">Loading history...</p> : null}{error ? <p className="form-error">{error}</p> : null}{!loading && !error && !visible.length ? <EmptyState title="No history yet" message="Saved activity for this category will appear here." /> : null}<div className="stack">{visible.map((item) => <article className="list-row" key={item.id}><div><strong>{item.title}</strong><p className="muted">{item.summary || item.entry_type}</p><p className="muted">Source: {item.source_app === "mobile" ? "Mobile app" : "Web app"}</p></div><span className="muted">{new Date(item.created_at).toLocaleString()}</span><details className="history-entry-details"><summary>View details</summary>{renderDetails(item)}</details></article>)}</div></Panel>;
}
