// Account creation screen. Public (middleware allowlists /signup). Mirrors the
// login screen: photographic hero with a frosted-glass card. `next` is the
// post-signup destination forwarded by the login link (so an invite deep link
// survives a sign-up detour), sanitised to same-origin paths only.

import SignupForm from "./SignupForm";
import Wordmark from "@/components/Wordmark";

function sanitiseNext(raw: string | undefined): string | null {
  if (!raw) return null;
  if (!raw.startsWith("/") || raw.startsWith("//")) return null;
  return raw;
}

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const safeNext = sanitiseNext(next);

  return (
    <div className="relative min-h-screen overflow-hidden bg-primary">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('/photography/hero-login.jpg')" }}
      />
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

          <p className="text-eyebrow text-secondary">Get started</p>
          <h1 className="text-display mt-3 text-primary">Create your account.</h1>

          <div className="mt-10">
            <SignupForm next={safeNext} />
          </div>
        </section>
      </main>
    </div>
  );
}
