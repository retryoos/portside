"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Wordmark from "@/components/Wordmark";

// Top app bar (DESIGN.md "Layout"): Laytimely wordmark on the left, pill nav
// tabs centred, account chip on the right. Shared chrome across every screen.
// Back navigation on detail pages is handled by BackArrowButton in the page
// content, not here.
const NAV = [
  { label: "Demurrage claim", href: "/cases" },
  { label: "Doc 2", href: "/doc-2" },
  { label: "Doc 3", href: "/doc-3" },
  { label: "Doc 4", href: "/doc-4" },
];

interface CurrentUser {
  sub: string;
  name: string;
}

export default function TopNav() {
  const pathname = usePathname() ?? "";

  return (
    <header className="fixed inset-x-0 top-0 z-30 border-b border-border bg-neutral/85 px-6 py-4 backdrop-blur md:px-8">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-6">
        <div className="flex items-center gap-8 md:gap-10">
          <Link href="/" className="text-primary" aria-label="Laytimely home">
            <Wordmark size="sm" />
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded-pill px-4 py-2 text-body-sm font-semibold transition-colors ${
                    active
                      ? "bg-primary text-on-primary"
                      : "text-secondary hover:bg-surface-muted hover:text-primary"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <AccountMenu />
      </div>
    </header>
  );
}

function AccountMenu() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Fetch the current user once on mount. A 401 leaves `user` null; the chip
  // just shows nothing. The middleware should already have redirected an
  // unauthed page load to /login, so this is mostly defensive.
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/auth/me", { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { user?: CurrentUser } | null) => {
        if (data?.user) setUser(data.user);
      })
      .catch(() => {
        /* ignore: chip simply stays empty */
      });
    return () => controller.abort();
  }, []);

  // Close on outside click + Escape.
  useEffect(() => {
    if (!open) return;
    function onClick(event: MouseEvent) {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function handleSignOut() {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      /* ignore: clearing the cookie locally is best-effort */
    }
    router.replace("/login");
    router.refresh();
  }

  // No user yet. Render an empty same-size slot so the header doesn't reflow.
  if (!user) {
    return <div aria-hidden className="h-10 w-10" />;
  }

  const initial = user.name.slice(0, 1).toUpperCase();

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className={`flex h-10 items-center gap-2.5 rounded-pill border border-border-strong bg-surface px-3 text-body-sm font-semibold text-primary transition-colors hover:bg-surface-muted ${
          open ? "bg-surface-muted" : ""
        }`}
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-[0.75rem] font-semibold text-on-primary">
          {initial}
        </span>
        <span className="hidden md:inline">{user.name}</span>
        <svg
          aria-hidden
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-3.5 w-3.5 text-secondary"
        >
          <path d="m4 6 4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-30 mt-2 w-60 overflow-hidden rounded-card border border-border bg-surface py-2 shadow-card"
        >
          <div className="px-4 py-2">
            <p className="text-eyebrow text-secondary">Signed in as</p>
            <p className="mt-1 truncate text-body-sm font-semibold text-primary">
              {user.name}
            </p>
          </div>
          <div className="my-1 h-px bg-border" />
          <Link
            href="/settings/inbox"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 text-left text-body-sm font-semibold text-primary transition-colors hover:bg-surface-muted"
          >
            Email-in setup
          </Link>
          <Link
            href="/settings/audit"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 text-left text-body-sm font-semibold text-primary transition-colors hover:bg-surface-muted"
          >
            Audit log
          </Link>
          <div className="my-1 h-px bg-border" />
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            disabled={signingOut}
            className="block w-full px-4 py-2.5 text-left text-body-sm font-semibold text-primary transition-colors hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-70"
          >
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      )}
    </div>
  );
}
