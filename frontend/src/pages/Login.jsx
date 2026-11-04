import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const USERNAME_PATTERN = /^[A-Za-z0-9_.-]{2,40}$/;

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login"); // "login" or "signup"
  const [form, setForm] = useState({ username: "", email: "", identifier: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isSignUp = mode === "signup";

  function update(field, value) {
    setForm((previous) => ({ ...previous, [field]: value }));
    setError("");
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
  }

  function validate() {
    if (isSignUp) {
      if (!USERNAME_PATTERN.test(form.username.trim())) {
        return "Username must be 2-40 characters: letters, numbers, dots, dashes or underscores.";
      }
      if (!EMAIL_PATTERN.test(form.email.trim())) return "Enter a valid email address.";
      if (form.password.length < 6) return "Password must be at least 6 characters.";
      return "";
    }
    if (!form.identifier.trim()) return "Enter your username or email.";
    if (!form.password) return "Enter your password.";
    return "";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (isSignUp) {
        await register(form.username.trim(), form.email.trim(), form.password);
      } else {
        await login(form.identifier.trim(), form.password);
      }
      // On success the app switches to the main screen automatically.
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit} noValidate>
        <div className="auth-brand">
          <span className="brand-mark">AI</span> Mock Interview
        </div>
        <div>
          <h1 className="auth-title">{isSignUp ? "Sign up" : "Log in"}</h1>
          <p className="page-subtitle">
            {isSignUp
              ? "Create your account to save your interviews and track your progress."
              : "Log in with your username or email to continue practising."}
          </p>
        </div>

        {isSignUp ? (
          <>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                value={form.username}
                onChange={(e) => update("username", e.target.value)}
                autoComplete="username"
                maxLength={40}
              />
              <div className="field-hint">Letters, numbers, dots, dashes or underscores.</div>
            </div>

            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                autoComplete="email"
                placeholder="you@gmail.com"
              />
            </div>
          </>
        ) : (
          <div className="field">
            <label htmlFor="identifier">Username or email</label>
            <input
              id="identifier"
              value={form.identifier}
              onChange={(e) => update("identifier", e.target.value)}
              autoComplete="username"
            />
          </div>
        )}

        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            autoComplete={isSignUp ? "new-password" : "current-password"}
          />
          {isSignUp ? <div className="field-hint">At least 6 characters.</div> : null}
        </div>

        {error ? (
          <div className="banner banner-error" role="alert">
            {error}
          </div>
        ) : null}

        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Please wait..." : isSignUp ? "Sign up" : "Log in"}
        </button>

        <p className="auth-switch">
          {isSignUp ? "Already have an account? " : "Don't have an account? "}
          <button
            type="button"
            className="link-button"
            onClick={() => switchMode(isSignUp ? "login" : "signup")}
          >
            {isSignUp ? "Log in" : "Sign up"}
          </button>
        </p>
      </form>
    </div>
  );
}