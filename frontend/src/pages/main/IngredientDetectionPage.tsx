import { useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { EmptyState, ErrorState, LoadingState } from "../../components/StateViews";

type DetectionResponse = {
  status: string;
  items: Array<{ name: string; confidence: number }>;
  candidates: Array<{ name: string; confidence: number }>;
};

function splitIngredients(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export function IngredientDetectionPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [manualCorrections, setManualCorrections] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<DetectionResponse | null>(null);
  const [error, setError] = useState("");

  const ingredients = useMemo(() => Array.from(new Set([
    ...(response?.items.map((item) => item.name) ?? []),
    ...splitIngredients(manualCorrections),
  ])), [manualCorrections, response]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const body = new FormData();
      body.append("image", file);
      if (manualCorrections.trim()) body.append("manual_corrections", manualCorrections);
      setResponse(await apiFetch<DetectionResponse>("/ingredients/detect/", { method: "POST", body }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Detection failed");
    } finally {
      setLoading(false);
    }
  }

  function openRecipe() {
    if (ingredients.length) navigate("/recipes", { state: { ingredients } });
  }

  return (
    <Panel title="Ingredient Detection" subtitle="Identify ingredients from an image.">
      <form className="stack" onSubmit={handleSubmit}>
        <label className="field"><span>Upload image</span><input type="file" accept="image/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        {file ? <div className="image-preview"><img src={URL.createObjectURL(file)} alt="Selected ingredient" /></div> : null}
        <label className="field"><span>Confirm or add ingredients (optional)</span><input value={manualCorrections} onChange={(event) => setManualCorrections(event.target.value)} placeholder="Add ingredients separated by commas" /></label>
        <button className="button button--primary" type="submit" disabled={loading || !file}>{loading ? "Detecting..." : "Detect ingredients"}</button>
      </form>
      {loading ? <LoadingState label="Scanning image..." /> : null}
      {error ? <ErrorState title="Detection failed" message={error} /> : null}
      {response ? <div className="result-list">
        {response.items.length ? <section className="result-card"><h2>Detected Ingredients</h2><div className="detected-list">
          {response.items.map((item) => <div key={item.name}><span className="success-mark">✓</span><strong>{item.name}</strong><span>{Math.round(item.confidence * 100)}%</span></div>)}
        </div></section> : <EmptyState title="Needs review" message="Confirm the ingredient or upload a clearer image." />}
        {response.candidates.length && !response.items.length ? <div className="stack"><p className="muted">Possible matches</p>{response.candidates.map((item) => <div className="result-item" key={item.name}><strong>{item.name}</strong><span>{Math.round(item.confidence * 100)}%</span></div>)}</div> : null}
        <div className="inline-form"><button className="button button--primary" type="button" onClick={openRecipe} disabled={!ingredients.length}>Generate Recipe</button></div>
      </div> : null}
    </Panel>
  );
}
