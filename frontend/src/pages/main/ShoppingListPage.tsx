import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { EmptyState } from "../../components/StateViews";
import type { ShoppingItem } from "../../types";

type ShoppingDraft = {
  name: string;
  quantity: string;
  category: string;
  notes: string;
};

const EMPTY_DRAFT: ShoppingDraft = {
  name: "",
  quantity: "",
  category: "General",
  notes: "",
};

export function ShoppingListPage() {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [draft, setDraft] = useState<ShoppingDraft>(EMPTY_DRAFT);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadItems() {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch<{ results: ShoppingItem[] }>("/shopping-items/");
      setItems(data.results ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load shopping items");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadItems();
    const interval = window.setInterval(() => void loadItems(), 15_000);
    return () => window.clearInterval(interval);
  }, []);

  function startEdit(item: ShoppingItem) {
    setEditingId(item.id);
    setDraft({
      name: item.name,
      quantity: item.quantity ?? "",
      category: item.category ?? "General",
      notes: item.notes ?? "",
    });
    setMessage("");
    setError("");
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft(EMPTY_DRAFT);
    setMessage("");
    setError("");
  }

  async function submitItem(event: FormEvent) {
    event.preventDefault();
    const name = draft.name.trim();
    if (!name) {
      setError("Item name is required.");
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload = {
        name,
        quantity: draft.quantity.trim(),
        category: draft.category.trim() || "General",
        notes: draft.notes.trim(),
      };
      if (editingId) {
        await apiFetch<ShoppingItem>(`/shopping-items/${editingId}/`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        setMessage("Shopping item updated.");
      } else {
        await apiFetch<ShoppingItem>("/shopping-items/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setMessage("Shopping item added.");
      }
      cancelEdit();
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save shopping item");
    } finally {
      setSaving(false);
    }
  }

  async function toggleItem(id: number, patch: Partial<Pick<ShoppingItem, "is_purchased" | "is_favorite">>) {
    setError("");
    try {
      await apiFetch<ShoppingItem>(`/shopping-items/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update item");
    }
  }

  async function deleteItem(id: number) {
    setError("");
    try {
      await apiFetch(`/shopping-items/${id}/`, { method: "DELETE" });
      if (editingId === id) {
        cancelEdit();
      }
      await loadItems();
      setMessage("Shopping item deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete item");
    }
  }

  return (
    <Panel title="Shopping List" subtitle="Add, update, and organize the ingredients you need.">
      <form className="stack" onSubmit={submitItem}>
        <div className="form-grid">
          <label className="field">
            <span>Item name</span>
            <input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Add an item" />
          </label>
          <label className="field">
            <span>Quantity</span>
            <input value={draft.quantity} onChange={(e) => setDraft((current) => ({ ...current, quantity: e.target.value }))} placeholder="Optional quantity" />
          </label>
          <label className="field">
            <span>Category</span>
            <input value={draft.category} onChange={(e) => setDraft((current) => ({ ...current, category: e.target.value }))} placeholder="Produce" />
          </label>
        </div>
        <label className="field">
          <span>Notes</span>
          <textarea value={draft.notes} onChange={(e) => setDraft((current) => ({ ...current, notes: e.target.value }))} rows={3} placeholder="Optional notes" />
        </label>
        <div className="inline-form">
          <button className="button button--primary" type="submit" disabled={saving}>
            {saving ? "Saving..." : editingId ? "Save changes" : "Add item"}
          </button>
          {editingId ? (
            <button className="button button--ghost" type="button" onClick={cancelEdit} disabled={saving}>
              Cancel edit
            </button>
          ) : null}
        </div>
      </form>
      {loading ? <p className="muted">Loading items...</p> : null}
      {message ? <p className="form-success">{message}</p> : null}
      {error ? <p className="form-error">{error}</p> : null}
      {!loading && items.length === 0 ? <EmptyState title="No items yet" message="Your shopping list is empty." /> : null}
      <div className="stack">
        {items.map((item) => (
          <article className="list-row" key={item.id}>
            <div className="stack">
              <div>
                <strong>{item.name}</strong>
                <p className="muted">
                  {item.category}
                  {item.quantity ? ` • ${item.quantity}` : ""}
                </p>
              </div>
              {item.notes ? <p className="muted">{item.notes}</p> : null}
            </div>
            <div className="stack stack--sm">
              <div className="pill-row">
                <button
                  type="button"
                  className={item.is_purchased ? "pill pill--done" : "pill"}
                  onClick={() => void toggleItem(item.id, { is_purchased: !item.is_purchased })}
                >
                  {item.is_purchased ? "Purchased" : "Mark purchased"}
                </button>
                <button
                  type="button"
                  className={item.is_favorite ? "pill pill--accent" : "pill"}
                  onClick={() => void toggleItem(item.id, { is_favorite: !item.is_favorite })}
                >
                  {item.is_favorite ? "Favorite" : "Mark favorite"}
                </button>
              </div>
              <div className="pill-row">
                <button type="button" className="pill" onClick={() => startEdit(item)}>
                  Edit
                </button>
                <button type="button" className="pill" onClick={() => void deleteItem(item.id)}>
                  Delete
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </Panel>
  );
}
