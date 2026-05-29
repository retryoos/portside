"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Top app bar (DESIGN.md "Layout"): "Portside" wordmark + pill nav tabs, active
// tab a soft-gray pill. Shared chrome across every screen.
const NAV = [
  { label: "Claims", href: "/cases" },
  { label: "Vessels", href: "/vessels" },
];

export default function TopNav() {
  const pathname = usePathname() ?? "";

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-neutral/85 px-6 py-3.5 backdrop-blur-md md:px-8">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-6">
        <div className="flex items-center gap-8">
          <Link
            href="/"
            className="flex items-center gap-2 text-h2 tracking-tight text-primary"
          >
            <Image
              src="/logo.png"
              alt=""
              aria-hidden
              width={31}
              height={31}
              priority
              className="h-[31px] w-[31px]"
            />
            Portside
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
        <span className="rounded-full border border-border px-3 py-1 text-label-caps text-secondary">
          Claims desk
        </span>
      </div>
    </header>
  );
}
