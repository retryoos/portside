import Image from "next/image";
import Link from "next/link";
import Container from "./Container";

// Marketing footer. Wordmark on the left, four short sitemap columns, a
// copyright line at the bottom. Off-white surface, hairline rule above.
const PRODUCT = [
  { label: "Demurrage workspace", href: "/login" },
  { label: "Edit with AI", href: "/login" },
  { label: "Pricing", href: "/#pricing" },
];

const COMPANY = [
  { label: "Contact", href: "/contact" },
  { label: "Security", href: "/security" },
];

const LEGAL = [
  { label: "Privacy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
];

export default function Footer() {
  return (
    <footer className="border-t border-border bg-neutral py-16 md:py-20">
      <Container>
        <div className="grid grid-cols-1 gap-12 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Link
              href="/"
              className="flex items-center gap-2.5 text-h3 tracking-tight text-primary"
            >
              <Image
                src="/logo.png"
                alt=""
                aria-hidden
                width={36}
                height={36}
                className="h-9 w-9"
              />
              <span>Papership.Ai</span>
            </Link>
            <p className="mt-5 max-w-sm text-body text-secondary">
              AI workflows for demurrage, laytime, freight disputes, and beyond.
            </p>
            <p className="mt-8 text-body-sm text-secondary">
              Athens · Greece
            </p>
          </div>

          <FooterColumn title="Product" links={PRODUCT} />
          <FooterColumn title="Company" links={COMPANY} />
          <FooterColumn title="Legal" links={LEGAL} />
        </div>

        <div className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-8 text-body-sm text-secondary">
          <p>© {new Date().getFullYear()} Papership.Ai. All rights reserved.</p>
          <p>
            Built in Athens by Dimitris, Panos &amp; Roman at the ACG AI Lab.
          </p>
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
  links: { label: string; href: string }[];
}) {
  return (
    <div>
      <p className="text-eyebrow text-secondary">{title}</p>
      <ul className="mt-5 space-y-3">
        {links.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              className="text-body-sm text-primary transition-colors hover:text-secondary"
            >
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
