import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FormActions, TextInput } from "../../components/Forms";
import { useAuth } from "../../context/AuthContext";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await signIn(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel auth-login-panel">
      <p className="auth-card__brand">SmartChef</p>
      <div className="panel__header">
        <div>
          <h2>Welcome back</h2>
          <p>Sign in to continue into SmartChef.</p>
        </div>
      </div>
      <form className="stack" onSubmit={handleSubmit}>
        <TextInput label="Email" value={email} onChange={setEmail} type="email" required />
        <TextInput label="Password" value={password} onChange={setPassword} type="password" required />
        {error ? <p className="form-error">{error}</p> : null}
        <FormActions submitting={submitting} label="Login" />
      </form>
      <div className="auth-card__links">
        <Link to="/forgot-password">Forgot password?</Link>
        <Link to="/signup">Create an account</Link>
      </div>
    </section>
  );
}
