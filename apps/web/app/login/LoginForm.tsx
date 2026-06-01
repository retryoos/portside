"use client";

// Sign-in form. Submits email + password to /api/auth/login (which proxies the
// backend and sets the session cookie), surfaces the server's error inline,
// and on success routes to `next` (or /cases). `router.refresh()` flushes
// server-component caches so the layout picks up the new session.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

const FIELD_CLASSES =
  "w-full rounded-md border border-border bg-surface px-4 py-3 text-body text-primary " +
  "placeholder:text-secondary/70 transition-colors " +
  "focus:border-primary focus:outline-none " +
  "disabled:cursor-not-allowed disabled:opacity-60";

export default function LoginForm({ next }: { next: string | null }) {
  const router = useRouter();
  const emailId = useId();
  const passwordId = useId();
  const errorId = useId();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const signupHref = next
    ? `/signup?next=${encodeURIComponent(next)}`
    : "/signup";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Sign in failed. Please try again.");
        setBusy(false);
        return;
      }

      router.replace(next ?? "/cases");
      router.refresh();
    } catch {
      setError("Network error. Check your connection and try again.");
      setBusy(false);
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label
          htmlFor={emailId}
          className="mb-2 block text-body-sm font-semibold text-primary"
        >
          Email
        </label>
        <input
          id={emailId}
          name="email"
          type="email"
          autoComplete="email"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          required
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={busy}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={FIELD_CLASSES}
        />
      </div>

      <div>
        <label
          htmlFor={passwordId}
          className="mb-2 block text-body-sm font-semibold text-primary"
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
        className="btn-lift mt-2 w-full rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-70"
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>

      <p className="pt-2 text-center text-body-sm text-secondary">
        New to Laytimely?{" "}
        <Link
          href={signupHref}
          className="font-semibold text-primary underline-offset-4 hover:underline"
        >
          Create an account
        </Link>
      </p>
    </form>
  );
}
