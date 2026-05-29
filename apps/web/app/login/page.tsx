// Sign-in screen. Public (the middleware allowlists /login). Layout mirrors
// the dashboard hero: gradient orb behind a soft white card, Portside wordmark
// above. Form interaction lives in the client component `LoginForm`.

import Image from "next/image";
import LoginForm from "./LoginForm";

// `next` is a post-login destination forwarded by the middleware. We
// sanitise it here so an attacker can't craft `/login?next=//evil.com` and
// hijack the redirect. Only same-origin paths are honoured.
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

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Decorative gradient orbs, same idiom as the /cases hero. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-32 -top-32 h-80 w-80 rounded-full bg-gradient-cool opacity-50 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-32 bottom-0 h-80 w-80 rounded-full bg-gradient-warm opacity-40 blur-3xl"
      />

      <main className="relative mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
        <div className="mb-8 flex items-center justify-center gap-2 text-h2 tracking-tight text-primary">
          Portside
          <Image
            src="/logo.png"
            alt=""
            aria-hidden
            width={31}
            height={31}
            priority
            className="h-[31px] w-[31px]"
          />
        </div>

        <section className="rounded-xl border border-border bg-surface px-7 py-8 shadow-[0_1px_2px_rgba(0,0,0,0.02)] md:px-8">
          <header className="mb-6">
            <h1 className="text-h1 text-primary">Sign in</h1>
            <p className="mt-2 text-body-sm text-secondary">
              Access the Portside claims desk.
            </p>
          </header>

          <LoginForm next={safeNext} />
        </section>

        <p className="mt-6 text-center text-body-sm text-secondary">
          <span className="text-label-caps text-secondary">Demo access</span>
          <br />
          Sign in with{" "}
          <span className="font-medium text-primary">admin</span> /{" "}
          <span className="font-medium text-primary">admin</span>.
        </p>
      </main>
    </div>
  );
}
