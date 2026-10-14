import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../../api/client";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../context/AuthContext";

export function SettingsPage() {
  const { profile, reload } = useAuth();
  const [notifications, setNotifications] = useState(profile?.notifications_enabled ?? true);
  const [language, setLanguage] = useState(profile?.language ?? "English");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setNotifications(profile?.notifications_enabled ?? true);
    setLanguage(profile?.language ?? "English");
  }, [profile]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await apiFetch("/profile/me/", {
      method: "PATCH",
      body: JSON.stringify({
        notifications_enabled: notifications,
        language,
      }),
    });
    setMessage("Settings saved.");
    await reload();
  }

  return (
    <Panel title="Settings" subtitle="Manage synced preferences and account behavior.">
      <form className="stack" onSubmit={handleSubmit}>
        <label className="field">
          <span>Notifications enabled</span>
          <select value={notifications ? "true" : "false"} onChange={(e) => setNotifications(e.target.value === "true")}>
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </label>
        <label className="field"><span>Language</span><input value={language} onChange={(e) => setLanguage(e.target.value)} /></label>
        <button className="button button--primary" type="submit">Save settings</button>
      </form>
      {message ? <p className="form-success">{message}</p> : null}
    </Panel>
  );
}
