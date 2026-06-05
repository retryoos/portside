"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Wordmark from "@/components/Wordmark";

// Top-of-page nav for the marketing surface. Transparent over the hero,
// solidifies into the neutral surface once the user scrolls past the first
// viewport. Compass + wordmark on the left, three text links + a sign-in
// pill on the right.
//
// The transparent style only makes sense on the landing page (``/``), which
// has a dark photographic hero. Meta pages like ``/contact`` and
// ``/security`` are white-on-white, so the nav would read as invisible
// when scrollY=0. We solidify by default on every route except ``/`` so
// the chrome is always visible and clickable.
// ``hard`` items navigate with a real <a> (full document load) instead of
// next/link, because /survey is a static document outside the Next route tree
// (served from public/survey via a rewrite); a client RSC navigation would 404.
const NAV: { label: string; href: string; hard?: boolean }[] = [
  { label: "How we work", href: "/#how-we-work" },
  { label: "Example", href: "/#example" },
  { label: "Resources", href: "/resources" },
  { label: "Engagement", href: "/#engagement" },
  { label: "Survey", href: "/survey", hard: true },
];

export default function MarketingNav() {
  const pathname = usePathname() ?? "/";
  const isLanding = pathname === "/";
  // Non-landing routes default to the solid scrolled style so the nav
  // never reads as invisible. On the landing page we still fade in
  // from transparent to solid as the user scrolls past the hero.
  const [scrolled, setScrolled] = useState(!isLanding);

  useEffect(() => {
    if (!isLanding) {
      setScrolled(true);
      return;
    }
    const onScroll = () => setScrolled(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [isLanding]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-30 transition-colors duration-200 ${
        scrolled
          ? "border-b border-border bg-neutral/85 backdrop-blur"
          : "border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-6 px-6 py-4 md:px-10">
        <Link
          href="/"
          aria-label="Laytimely home"
          className={scrolled ? "text-primary" : "text-on-primary"}
        >
          <Wordmark size="sm" />
        </Link>
        <nav className="hidden items-center gap-2 md:flex">
          {NAV.map((item) => {
            const className = `rounded-pill px-4 py-2 text-body-sm font-semibold transition-colors ${
              scrolled
                ? "text-secondary hover:bg-surface-muted hover:text-primary"
                : "text-on-primary/80 hover:bg-on-primary/10 hover:text-on-primary"
            }`;
            return item.hard ? (
              <a key={item.href} href={item.href} className={className}>
                {item.label}
              </a>
            ) : (
              <Link key={item.href} href={item.href} className={className}>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/login"
          className={`btn-lift rounded-pill px-5 py-2.5 text-body-sm font-semibold ${
            scrolled
              ? "bg-cta text-on-cta hover:bg-cta-hover"
              : "bg-cta-inverse text-on-cta-inverse hover:bg-cta-inverse-hover"
          }`}
        >
          Sign in
        </Link>
      </div>
    </header>
  );
}
