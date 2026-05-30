"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

// Top app bar (DESIGN.md "Layout"): "Papership.Ai" wordmark + pill nav tabs, active
// tab a soft-gray pill. Shared chrome across every screen. The right-side chip
// is the account menu (display name + Sign out); it fetches the current user
// from /api/auth/me on mount. Back navigation on detail pages is handled by
// the floating BackArrowButton component placed in the page content, not here.
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
    <header className="fixed inset-x-0 top-0 z-30 border-b border-border bg-surface px-6 py-3.5 md:px-8">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-6">
        <div className="flex items-center gap-6 md:gap-8">
          <Link
            href="/"
            className="flex items-center gap-2 text-h2 tracking-tight text-primary"
          >
            <Image
              src="/logo.png"
              alt=""
              aria-hidden
              width={36}
              height={36}
              priority
              className="h-[36px] w-[36px]"
            />
            Papership.Ai
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
                  className={`rounded-full px-3.5 py-1.5 text-body-sm font-medium transition-colors ${
                    active
                      ? "bg-surface-muted text-primary"
                      : "text-secondary hover:bg-surface-muted/70 hover:text-primary"
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
    return <div aria-hidden className="h-9 w-9" />;
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className={`flex h-9 w-9 items-center justify-center rounded-full text-primary transition-colors ${
          open ? "bg-surface-muted" : ""
        }`}
      >
        <svg
          aria-hidden
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-5 w-5"
        >
          {/* Head + shoulders silhouette. Single rounded path, fills with
              currentColor so it inherits the button's text-primary (near-black). */}
          <path d="M12 12.5a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5zm0 1.75c-3.4 0-8.5 1.7-8.5 5.1V21h17v-1.65c0-3.4-5.1-5.1-8.5-5.1z" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-30 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-surface py-1.5 shadow-[0_4px_24px_rgba(0,0,0,0.06)]"
        >
          <div className="px-3 py-2">
            <p className="text-label-caps text-secondary">Signed in as</p>
            <p className="mt-0.5 truncate text-body-sm font-medium text-primary">
              {user.name}
            </p>
          </div>
          <div className="my-1 h-px bg-border" />
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            disabled={signingOut}
            className="block w-full px-3 py-2 text-left text-body-sm text-primary transition-colors hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-70"
          >
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      )}
    </div>
  );
}
