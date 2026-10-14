import { Link } from "react-router-dom";
import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../context/AuthContext";

export function ProfilePage() {
  const { profile, user, reload, signOut } = useAuth();
  const [displayName, setDisplayName] = useState(profile?.display_name ?? "");
  const [theme, setTheme] = useState<"system" | "light" | "dark">(profile?.theme_preference ?? "system");
  const [unit, setUnit] = useState<"metric" | "imperial">(profile?.unit_preference ?? "metric");
  const [message, setMessage] = useState("");
  const [aboutOpen, setAboutOpen] = useState(false);

  useEffect(() => {
    setDisplayName(profile?.display_name ?? "");
    setTheme(profile?.theme_preference ?? "system");
    setUnit(profile?.unit_preference ?? "metric");
  }, [profile]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await apiFetch("/profile/me/", {
      method: "PATCH",
      body: JSON.stringify({
        display_name: displayName,
        theme_preference: theme,
        unit_preference: unit,
      }),
    });
    setMessage("Profile updated.");
    await reload();
  }

  return (
    <Panel title="Profile" subtitle="Your authenticated SmartChef account and preferences.">
      <div className="profile-summary">
        <div className="profile-avatar" aria-hidden="true">{(profile?.display_name || user?.email || "S").charAt(0).toUpperCase()}</div>
        <div>
          <p className="muted">Account</p>
          <h3>{profile?.display_name || user?.email}</h3>
          <p className="muted">{user?.email}</p>
        </div>
      </div>
      <div className="profile-account-grid">
        <div className="result-item"><strong>User ID</strong><span>{user?.id ?? "—"}</span></div>
        <div className="result-item"><strong>Email</strong><span>{user?.email ?? "—"}</span></div>
      </div>
      <div className="profile-actions">
        <Link className="button" to="/settings">Settings <span aria-hidden="true">→</span></Link>
        <button className="button" type="button" onClick={() => setAboutOpen((open) => !open)}>About <span aria-hidden="true">{aboutOpen ? "↑" : "→"}</span></button>
        <button className="button button--primary" type="button" onClick={() => void signOut()}>Sign Out</button>
      </div>
      {aboutOpen ? <div className="result-card profile-about"><h2>About SmartChef</h2><p className="muted">SmartChef combines ingredient recognition, scale reading, nutrition, recipes, planning, and shared account history.</p><p className="muted">Your profile and history are loaded from the authenticated Django account.</p></div> : null}
      <form className="stack" onSubmit={handleSubmit}>
        <label className="field"><span>Display name</span><input value={displayName} onChange={(e) => setDisplayName(e.target.value)} /></label>
        <label className="field">
          <span>Theme</span>
          <select value={theme} onChange={(e) => setTheme(e.target.value as "system" | "light" | "dark")}>
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
        <label className="field">
          <span>Units</span>
          <select value={unit} onChange={(e) => setUnit(e.target.value as "metric" | "imperial")}>
            <option value="metric">Metric</option>
            <option value="imperial">Imperial</option>
          </select>
        </label>
        <button className="button button--primary" type="submit">Save profile</button>
      </form>
      {message ? <p className="form-success">{message}</p> : null}
    </Panel>
  );
}
