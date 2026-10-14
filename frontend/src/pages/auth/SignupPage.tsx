import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { FormActions, TextInput } from "../../components/Forms";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../context/AuthContext";

export function SignupPage() {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { signUp } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await signUp({ display_name: displayName, email, password });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel title="Create account" subtitle="One account works for both Flutter and the web app.">
      <form className="stack" onSubmit={handleSubmit}>
        <TextInput label="Display name" value={displayName} onChange={setDisplayName} required />
        <TextInput label="Email" value={email} onChange={setEmail} type="email" required />
        <TextInput label="Password" value={password} onChange={setPassword} type="password" required />
        {error ? <p className="form-error">{error}</p> : null}
        <FormActions submitting={submitting} label="Create account" />
      </form>
    </Panel>
  );
}
