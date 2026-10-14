import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { NutritionResult } from "../../components/ResultCards";

type ScanResponse = { ingredient: string | null; weight_grams: number | null; ingredient_detected: boolean; weight_detected: boolean; candidates: Array<{ name: string; confidence: number }>; message?: string };

export function NutritionPage() {
  const fileInput = useRef<HTMLInputElement>(null); const cameraInput = useRef<HTMLInputElement>(null);
  const scanSequence = useRef(0);
  const [ingredient, setIngredient] = useState(""); const [grams, setGrams] = useState(""); const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null); const [nutrition, setNutrition] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function selectFile(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    scanSequence.current += 1;
    setFile(selected);
    setIngredient("");
    setGrams("");
    setScanResult(null);
    setNutrition(null);
    setError("");
    // Allow selecting the same file again after a scan.
    event.target.value = "";
  }

  async function scanImage(event: FormEvent) {
    event.preventDefault(); if (!file) return;
    const requestSequence = scanSequence.current;
    setLoading(true); setError(""); setScanResult(null); setNutrition(null);
    try {
      const body = new FormData(); body.append("image", file);
      if (ingredient.trim()) body.append("ingredient", ingredient.trim()); if (grams) body.append("grams", grams);
      const result = await apiFetch<ScanResponse>("/nutrition/scan/", { method: "POST", body });
      if (requestSequence !== scanSequence.current) return;
      setScanResult(result); setIngredient(result.ingredient ?? ingredient); setGrams(result.weight_grams ? String(result.weight_grams) : grams);
      if (result.ingredient && result.weight_grams) await calculateNutrition(result.ingredient, result.weight_grams, requestSequence);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not analyze the image"); } finally { setLoading(false); }
  }
  async function calculateNutrition(detectedIngredient = ingredient, detectedGrams = Number(grams), requestSequence = scanSequence.current) {
    if (!detectedIngredient.trim() || !detectedGrams) return;
    setLoading(true); setError("");
    try {
      const result = await apiFetch<{ matches: Record<string, any>[] }>("/nutrition/lookup/", { method: "POST", body: JSON.stringify({ ingredient: detectedIngredient.trim(), grams: detectedGrams }) });
      if (requestSequence !== scanSequence.current) return;
      if (!result.matches.length) throw new Error("No nutrition data was found for this ingredient."); setNutrition(result.matches[0]);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not calculate nutrition"); } finally { setLoading(false); }
  }
  return <Panel title="Nutrition Analysis" subtitle="Detect an ingredient and digital scale weight from one image, then calculate its serving nutrition.">
    <form className="scan-panel stack" onSubmit={scanImage}><h2>Image scan</h2><p className="muted">Upload a photo containing the ingredient and scale display.</p>
      <div className="pill-row"><button className="button" type="button" onClick={() => cameraInput.current?.click()}>Take Photo</button><button className="button" type="button" onClick={() => fileInput.current?.click()}>Upload Image</button></div>
      <input ref={cameraInput} hidden type="file" accept="image/*" capture="environment" onChange={selectFile} /><input ref={fileInput} hidden type="file" accept="image/*" onChange={selectFile} />
      {file && previewUrl ? <div className="image-preview"><img src={previewUrl} alt="Ingredient and weighing display" /></div> : <div className="scan-empty"><strong>No image selected</strong><span>Choose a photo showing the ingredient and display.</span></div>}
      <button className="button button--primary" type="submit" disabled={loading || !file}>{loading ? "Analyzing image..." : "Detect ingredient and weight"}</button></form>
    {error ? <p className="form-error">{error}</p> : null}
    {scanResult ? <div className="result-sections"><section className="result-card"><h2>Detection result</h2><div className="result-item"><strong>Detected ingredient</strong><span>{scanResult.ingredient ?? "Not detected"}</span></div><div className="result-item"><strong>Detected weight</strong><span>{scanResult.weight_grams ? `${scanResult.weight_grams} g` : "Not detected"}</span></div>{scanResult.message ? <p className="muted">{scanResult.message}</p> : null}
      <label className="field"><span>Edit ingredient (fallback)</span><input value={ingredient} onChange={(event) => setIngredient(event.target.value)} placeholder="Example: tomato" /></label><label className="field"><span>Edit weight in grams (fallback)</span><input value={grams} onChange={(event) => setGrams(event.target.value)} type="number" min="0.1" max="10000" /></label><button className="button button--primary" type="button" disabled={loading || !ingredient.trim() || !Number(grams)} onClick={() => void calculateNutrition()}>{loading ? "Calculating nutrition..." : "Analyze Nutrition"}</button></section>
      {nutrition ? <section className="result-card"><h2>Nutrition results</h2><p className="muted">Calculated for {grams} g of {ingredient}.</p><NutritionResult match={nutrition} /></section> : null}</div> : null}
  </Panel>;
}
