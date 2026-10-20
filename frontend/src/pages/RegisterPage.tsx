import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { AuthFrame } from "../components/AuthFrame";
import { errorText } from "../lib/errors";
import { registerSchema, type RegisterValues } from "../lib/schemas";
import { useAuthStore } from "../store/auth";

export function RegisterPage() {
  const access = useAuthStore((state) => state.access);
  const setSession = useAuthStore((state) => state.setSession);
  const [error, setError] = useState("");
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", password: "", confirm: "" },
  });

  if (access) return <Navigate to="/" replace />;

  return (
    <AuthFrame>
      <form
        className="stack"
        onSubmit={form.handleSubmit(async (values) => {
          setError("");
          try {
            const session = await api.auth.register(values.username, values.password);
            setSession(session.access, session.refresh, session.username);
          } catch (caught) {
            setError(errorText(caught, "The account could not be created."));
          }
        })}
      >
        <div>
          <p className="kicker">Register</p>
          <h2>Start a maintainer log</h2>
        </div>
        <label className="field">
          <span>Username</span>
          <input autoComplete="username" {...form.register("username")} />
        </label>
        {form.formState.errors.username && <p className="error">{form.formState.errors.username.message}</p>}
        <label className="field">
          <span>Password</span>
          <input type="password" autoComplete="new-password" {...form.register("password")} />
        </label>
        {form.formState.errors.password && <p className="error">{form.formState.errors.password.message}</p>}
        <label className="field">
          <span>Confirm password</span>
          <input type="password" autoComplete="new-password" {...form.register("confirm")} />
        </label>
        {form.formState.errors.confirm && <p className="error">{form.formState.errors.confirm.message}</p>}
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={form.formState.isSubmitting}>
          Create account
        </button>
        <p className="muted">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </AuthFrame>
  );
}
