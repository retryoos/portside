"use client";

// Sign-in form. Submits to /api/auth/login, surfaces the server's error
// message inline, and on success routes to `next` (or /cases). `router.refresh()`
// flushes server-component caches so the layout picks up the new session.

import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

const FIELD_CLASSES =
  "w-full rounded-md border border-border bg-surface px-3.5 py-2.5 text-body text-primary " +
  "placeholder:text-secondary/70 transition-colors " +
  "focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 " +
  "disabled:cursor-not-allowed disabled:opacity-60";

export default function LoginForm({ next }: { next: string | null }) {
  const router = useRouter();
  const usernameId = useId();
  const passwordId = useId();
  const errorId = useId();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Sign in failed. Please try again.");
        setBusy(false);
        return;
      }

      // Hard refresh so the server layout and middleware see the new cookie.
      router.replace(next ?? "/cases");
      router.refresh();
    } catch {
      setError("Network error. Check your connection and try again.");
      setBusy(false);
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label
          htmlFor={usernameId}
          className="mb-1.5 block text-body-sm font-medium text-primary"
        >
          Username
        </label>
        <input
          id={usernameId}
          name="username"
          type="text"
          autoComplete="username"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          required
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={busy}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={FIELD_CLASSES}
        />
      </div>

      <div>
        <label
          htmlFor={passwordId}
          className="mb-1.5 block text-body-sm font-medium text-primary"
        >
          Password
        </label>
        <input
          id={passwordId}
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={FIELD_CLASSES}
        />
      </div>

      {error && (
        <p
          id={errorId}
          role="alert"
          className="rounded-md bg-danger-container px-3 py-2 text-body-sm text-danger"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="mt-2 w-full rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-70"
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
