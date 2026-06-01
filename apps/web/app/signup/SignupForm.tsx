"use client";

// Account creation form. Posts name + email + password to /api/auth/signup
// (which proxies the backend and sets the session cookie), then routes to
// `next` (or /cases). Client-side validation mirrors the backend so obvious
// mistakes are caught before the round trip; the server stays the source of
// truth (duplicate email, rate limit).

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

const FIELD_CLASSES =
  "w-full rounded-md border border-border bg-surface px-4 py-3 text-body text-primary " +
  "placeholder:text-secondary/70 transition-colors " +
  "focus:border-primary focus:outline-none " +
  "disabled:cursor-not-allowed disabled:opacity-60";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MIN_PASSWORD = 8;

export default function SignupForm({ next }: { next: string | null }) {
  const router = useRouter();
  const nameId = useId();
  const emailId = useId();
  const passwordId = useId();
  const errorId = useId();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loginHref = next ? `/login?next=${encodeURIComponent(next)}` : "/login";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError(null);

    const trimmedEmail = email.trim();
    if (!EMAIL_RE.test(trimmedEmail)) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < MIN_PASSWORD) {
      setError(`Password must be at least ${MIN_PASSWORD} characters.`);
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: trimmedEmail,
          password,
          name: name.trim() || null,
        }),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Could not create the account. Try again.");
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
          htmlFor={nameId}
          className="mb-2 block text-body-sm font-semibold text-primary"
        >
          Name <span className="font-normal text-secondary">(optional)</span>
        </label>
        <input
          id={nameId}
          name="name"
          type="text"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={busy}
          className={FIELD_CLASSES}
        />
      </div>

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
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={FIELD_CLASSES}
        />
        <p className="mt-1.5 text-body-sm text-secondary">
          At least {MIN_PASSWORD} characters.
        </p>
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
        {busy ? "Creating account…" : "Create account"}
      </button>

      <p className="pt-2 text-center text-body-sm text-secondary">
        Already have an account?{" "}
        <Link
          href={loginHref}
          className="font-semibold text-primary underline-offset-4 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}
