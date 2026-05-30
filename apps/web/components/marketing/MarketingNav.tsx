"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Wordmark from "@/components/Wordmark";

// Top-of-page nav for the marketing surface. Transparent over the hero,
// solidifies into the neutral surface once the user scrolls past the first
// viewport. Compass + wordmark on the left, three text links + a sign-in
// pill on the right.
const NAV = [
  { label: "Product", href: "#product" },
  { label: "How it works", href: "#how" },
  { label: "Pricing", href: "#pricing" },
];

export default function MarketingNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

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
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-pill px-4 py-2 text-body-sm font-semibold transition-colors ${
                scrolled
                  ? "text-secondary hover:bg-surface-muted hover:text-primary"
                  : "text-on-primary/80 hover:bg-on-primary/10 hover:text-on-primary"
              }`}
            >
              {item.label}
            </Link>
          ))}
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
