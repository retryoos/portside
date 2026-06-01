"use client";

// "Try the live demo" CTA for the marketing site. Posts to /api/auth/demo,
// which mints a demo session cookie, then lands the visitor in the populated
// cases dashboard. Styling is passed in via `className` so the same button
// can sit in the hero (pill, inverse) or the nav (compact) without forking.

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function DemoButton({
  className,
  children = "Try the live demo",
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  async function startDemo() {
    if (busy) return;
    setBusy(true);
    setError(false);
    try {
      const res = await fetch("/api/auth/demo", { method: "POST" });
      if (!res.ok) {
        setError(true);
        setBusy(false);
        return;
      }
      router.replace("/cases");
      router.refresh();
    } catch {
      setError(true);
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={startDemo}
      disabled={busy}
      className={className}
      aria-live="polite"
    >
      {busy ? "Starting…" : error ? "Try again" : children}
    </button>
  );
}
