import Link from "next/link";
import Container from "./Container";
import Wordmark from "@/components/Wordmark";

// Marketing footer. Wordmark on the left, four short sitemap columns, a
// copyright line at the bottom. Off-white surface, hairline rule above.
//
// Two product links currently point at /login (the authed product is
// behind that gate); keys are by label rather than href so the duplicate
// href does not produce a React "two children with the same key" warning.
// ``hard`` links navigate with a real <a> (full load) instead of next/link;
// /survey is a static document outside the Next route tree (see MarketingNav).
type FooterLink = { label: string; href: string; hard?: boolean };

const STUDIO: FooterLink[] = [
  { label: "How we work", href: "/#how-we-work" },
  { label: "Example system", href: "/#example" },
  { label: "Engagement", href: "/#engagement" },
  { label: "Open the app", href: "/login" },
];

const COMPANY: FooterLink[] = [
  { label: "About", href: "/about" },
  { label: "Survey", href: "/survey", hard: true },
  { label: "Contact", href: "/contact" },
  { label: "Security", href: "/security" },
];

const LEGAL: FooterLink[] = [
  { label: "Privacy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
];

export default function Footer() {
  return (
    <footer className="border-t border-border bg-neutral py-16 md:py-20">
      <Container>
        <div className="grid grid-cols-1 gap-12 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="text-primary" aria-label="Laytimely home">
              <Wordmark size="sm" />
            </Link>
            <p className="mt-5 max-w-sm text-body text-secondary">
              Custom multi-agent AI systems for maritime operations. The
              demurrage engine is one we shipped.
            </p>
            <p className="mt-8 text-body-sm text-secondary">
              Athens, Greece
            </p>
          </div>

          <FooterColumn title="Studio" links={STUDIO} />
          <FooterColumn title="Company" links={COMPANY} />
          <FooterColumn title="Legal" links={LEGAL} />
        </div>

        <div className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-8 text-body-sm text-secondary">
          <p>© {new Date().getFullYear()} Laytimely. All rights reserved.</p>
          <p>Built in Athens by Dimitris &amp; Roman at the ACG AI Lab.</p>
        </div>
      </Container>
    </footer>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: FooterLink[];
}) {
  const linkClass =
    "text-body-sm text-primary transition-colors hover:text-secondary";
  return (
    <div>
      <p className="text-eyebrow text-secondary">{title}</p>
      <ul className="mt-5 space-y-3">
        {links.map((l) => (
          // Key by ``label`` since links can share an href; href-based keys
          // would collide.
          <li key={l.label}>
            {l.hard ? (
              <a href={l.href} className={linkClass}>
                {l.label}
              </a>
            ) : (
              <Link href={l.href} className={linkClass}>
                {l.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
