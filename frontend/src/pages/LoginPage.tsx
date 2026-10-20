import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { AuthFrame } from "../components/AuthFrame";
import { errorText } from "../lib/errors";
import { loginSchema, type LoginValues } from "../lib/schemas";
import { useAuthStore } from "../store/auth";

export function LoginPage() {
  const access = useAuthStore((state) => state.access);
  const setSession = useAuthStore((state) => state.setSession);
  const [error, setError] = useState("");
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  if (access) return <Navigate to="/" replace />;

  return (
    <AuthFrame>
      <form
        className="stack"
        onSubmit={form.handleSubmit(async (values) => {
          setError("");
          try {
            const tokens = await api.auth.login(values.username, values.password);
            setSession(tokens.access, tokens.refresh, values.username);
          } catch (caught) {
            setError(errorText(caught, "Those credentials were not accepted."));
          }
        })}
      >
        <div>
          <p className="kicker">Sign in</p>
          <h2>Open your log</h2>
        </div>
        <label className="field">
          <span>Username</span>
          <input autoComplete="username" {...form.register("username")} />
        </label>
        {form.formState.errors.username && <p className="error">{form.formState.errors.username.message}</p>}
        <label className="field">
          <span>Password</span>
          <input type="password" autoComplete="current-password" {...form.register("password")} />
        </label>
        {form.formState.errors.password && <p className="error">{form.formState.errors.password.message}</p>}
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={form.formState.isSubmitting}>
          Sign in
        </button>
        <p className="muted">
          New here? <Link to="/register">Register the maintainer account</Link>
        </p>
      </form>
    </AuthFrame>
  );
}
