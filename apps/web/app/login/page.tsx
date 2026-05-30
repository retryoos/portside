// Sign-in screen. Public (the middleware allowlists /login). Layout mirrors
// the dashboard hero: gradient orb behind a soft white card, Papership.Ai wordmark
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
      <main className="relative mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
        <div className="mb-10 flex flex-col items-center text-center text-primary">
          <div className="flex items-center gap-3 text-display tracking-tight">
            <Image
              src="/logo.png"
              alt=""
              aria-hidden
              width={56}
              height={56}
              priority
              className="h-[56px] w-[56px]"
            />
            Papership.Ai
          </div>
          <div className="mt-3 text-[1.25rem] leading-snug text-primary">
            automated maritime paperwork
          </div>
        </div>

        <section className="rounded-xl border border-border bg-surface px-7 py-8 shadow-[0_1px_2px_rgba(0,0,0,0.02)] md:px-8">
          <header className="mb-6">
            <h1 className="text-h1 text-primary">Sign in</h1>
          </header>

          <LoginForm next={safeNext} />
        </section>
      </main>
    </div>
  );
}
