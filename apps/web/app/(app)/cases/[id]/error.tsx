"use client";

import Link from "next/link";

// Route error boundary for a single claim. A render crash here (for example a
// voyage that ended in an "error" state with missing fields, or a transient
// data problem) is caught and shown as a recoverable message instead of
// white-screening the whole app with "Application error".
export default function CaseError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-[1240px] flex-col items-center justify-center gap-6 px-6 text-center">
      <div>
        <p className="text-eyebrow text-secondary">Something went wrong</p>
        <h1 className="mt-3 text-h2 text-primary">
          We could not load this claim.
        </h1>
        <p className="mt-3 max-w-md text-body text-secondary">
          This can happen if the claim is still processing or ended in an error
          state. Try again, or head back to your cases.
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
        >
          Try again
        </button>
        <Link
          href="/cases"
          className="btn-lift rounded-pill border border-border-strong px-6 py-3 text-body-sm font-semibold text-primary hover:bg-surface-muted"
        >
          Back to cases
        </Link>
      </div>
    </main>
  );
}
