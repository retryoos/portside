// Sign-in screen. Public (the middleware allowlists /login). Photographic
// hero with a frosted-glass card overlaid asymmetrically (Revolut-style),
// falling back to a deep-ink surface when no hero photo is committed.

import ReactDOM from "react-dom";
import LoginForm from "./LoginForm";
import Wordmark from "@/components/Wordmark";

// `next` is a post-login destination forwarded by the middleware. Sanitised
// here so an attacker can't craft `/login?next=//evil.com` and hijack the
// redirect. Only same-origin paths are honoured.
function sanitiseNext(raw: string | undefined): string | null {
  if (!raw) return null;
  if (!raw.startsWith("/") || raw.startsWith("//")) return null;
  return raw;
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const safeNext = sanitiseNext(next);

  // Preload the login hero so it loads with the page, not a beat after.
  ReactDOM.preload("/photography/hero-login.jpg", {
    as: "image",
    fetchPriority: "high",
  });

  return (
    <div className="relative min-h-screen overflow-hidden bg-primary">
      {/* Hero photograph layer. Falls back transparently to bg-primary if the
          asset is not yet committed (DESIGN.md photography section). */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: "url('/photography/hero-login.jpg')",
        }}
      />
      {/* Subtle ink scrim so the glass card always reads, even on a bright photo. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, rgba(0,0,0,0.22) 0%, rgba(0,0,0,0.05) 45%, rgba(0,0,0,0) 70%)",
        }}
      />

      <main className="relative flex min-h-screen flex-col justify-center px-6 py-16 md:items-end md:px-16 md:py-20 lg:px-24">
        <section className="card-glass w-full max-w-md px-8 py-10 md:px-10 md:py-12">
          <div className="mb-10">
            <Wordmark size="lg" />
          </div>

          <p className="text-eyebrow text-secondary">Welcome back</p>
          <h1 className="text-display mt-3 text-primary">Sign in.</h1>

          <div className="mt-10">
            <LoginForm next={safeNext} />
          </div>
        </section>
      </main>
    </div>
  );
}
