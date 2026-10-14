import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { FormActions, TextInput } from "../../components/Forms";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../context/AuthContext";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { resetPassword } = useAuth();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const response = await resetPassword(email);
      setMessage(response.detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel title="Forgot password" subtitle="Request a reset email from the backend.">
      <form className="stack" onSubmit={handleSubmit}>
        <TextInput label="Email" value={email} onChange={setEmail} type="email" required />
        {message ? <p className="form-success">{message}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        <FormActions submitting={submitting} label="Send reset link" />
        <Link className="inline-link" to="/login">
          Back to login
        </Link>
      </form>
    </Panel>
  );
}
