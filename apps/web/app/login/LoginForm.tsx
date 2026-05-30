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

      <div className="flex items-center gap-3 pt-2" aria-hidden="true">
        <span className="h-px flex-1 bg-border" />
        <span className="text-label-caps text-secondary">or</span>
        <span className="h-px flex-1 bg-border" />
      </div>

      <div className="space-y-2.5">
        <button
          type="button"
          disabled={busy}
          className="flex w-full items-center justify-center gap-2.5 rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-70"
        >
          <GoogleIcon />
          Sign in with Google
        </button>
        <button
          type="button"
          disabled={busy}
          className="flex w-full items-center justify-center gap-2.5 rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-70"
        >
          <MicrosoftIcon />
          Sign in with Microsoft
        </button>
      </div>
    </form>
  );
}

function GoogleIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
    >
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.56c2.08-1.92 3.28-4.74 3.28-8.09Z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.56-2.76c-.99.66-2.25 1.06-3.72 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.11A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.44.34-2.11V7.05H2.18A11 11 0 0 0 1 12c0 1.78.43 3.47 1.18 4.95l3.66-2.84Z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.05l3.66 2.84C6.71 7.3 9.14 5.38 12 5.38Z"
      />
    </svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4">
      <path fill="#F25022" d="M2 2h9.5v9.5H2z" />
      <path fill="#7FBA00" d="M12.5 2H22v9.5h-9.5z" />
      <path fill="#00A4EF" d="M2 12.5h9.5V22H2z" />
      <path fill="#FFB900" d="M12.5 12.5H22V22h-9.5z" />
    </svg>
  );
}
