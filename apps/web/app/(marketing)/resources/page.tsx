import type { Metadata } from "next";
import Link from "next/link";
import Section from "@/components/marketing/Section";
import ScrollReveal from "@/components/marketing/ScrollReveal";

// Title omits the brand: the root layout template appends ", Laytimely".
export const metadata: Metadata = {
  title: "Resources",
  description:
    "The English maritime authorities behind our laytime and demurrage analysis, and the references we trust. Check our work.",
};

// The real authorities our demurrage system draws on. Plain-English notes, not
// legal advice. Listing them (with full citations) is the point: it shows the
// citations are genuine and checkable, which is what a laytime professional
// will look for. Sourced from our legal corpus (apps/api/.../legal/corpus.jsonl).
const AUTHORITIES = [
  {
    citation: "The Johanna Oldendorff [1974] AC 479",
    topic: "Arrived ship",
    note: "A vessel only counts as 'arrived', so notice of readiness can be tendered, once she is at the charterer's immediate and effective disposition within the port (the Reid test).",
  },
  {
    citation: "The Mexico 1 [1990] 1 Lloyd's Rep 507",
    topic: "Weather exception",
    note: "A stoppage comes off laytime only when the express contractual condition for the exception is actually met. The master's view that work was unworkable is not enough.",
  },
  {
    citation: "The Tres Flores [1973] 2 Lloyd's Rep 247",
    topic: "Notice of readiness",
    note: "A notice of readiness is invalid if the vessel is not in fact ready in all respects when it is tendered, including holds clean and fit to load.",
  },
  {
    citation: "The Forum Craftsman [1985] 1 Lloyd's Rep 291",
    topic: "Once on demurrage",
    note: "Once a vessel is on demurrage, laytime exceptions stop applying unless the charter party expressly extends them. 'Once on demurrage, always on demurrage.'",
  },
  {
    citation: "President of India v Lips Maritime Corp [1988] AC 395",
    topic: "Nature of demurrage",
    note: "Demurrage is liquidated damages for detaining the vessel beyond the agreed laytime, not freight and not a separate cause of action.",
  },
  {
    citation: "The Jay Bola [1997] 2 Lloyd's Rep 279",
    topic: "Time bar",
    note: "Time-bar clauses are read strictly. A claim filed late, without meeting the clause's procedural requirements, is barred whatever its merits.",
  },
];

const REFERENCES = [
  {
    name: "BIMCO",
    href: "https://www.bimco.org/",
    note: "The standard charter party forms and clauses our systems read, from GENCON to the tanker and dry-bulk pro formas.",
  },
  {
    name: "LMAA",
    href: "https://www.lmaa.london/",
    note: "The London Maritime Arbitrators Association, where most charter party disputes are actually decided. Demurrage goes to arbitration, not court.",
  },
  {
    name: "BAILII",
    href: "https://www.bailii.org/",
    note: "Free full text of the English cases above. Search the citation to read the judgment in full.",
  },
];

export default function ResourcesPage() {
  return (
    <main className="pt-24">
      <Section>
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Resources</p>
          <h1 className="text-display mt-6 max-w-3xl text-primary">
            The laytime authorities behind our analysis.
          </h1>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            We cite real English maritime law. These are some of the cases our
            demurrage system draws on, in plain English. They are background, not
            legal advice. Check our work.
          </p>
        </ScrollReveal>

        <div className="mt-16">
          {AUTHORITIES.map((a, i) => (
            <ScrollReveal key={a.citation} delayMs={60 * (i + 1)}>
              <div className="grid grid-cols-1 gap-3 border-t border-border-strong py-7 md:grid-cols-[1.1fr_1.4fr] md:gap-12">
                <div>
                  <p className="text-eyebrow text-secondary">{a.topic}</p>
                  <p className="mt-3 text-h3 text-primary">{a.citation}</p>
                </div>
                <p className="text-body-lg text-secondary">{a.note}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </Section>

      <Section tone="muted">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">References we trust</p>
          <h2 className="text-display mt-6 max-w-3xl text-primary">
            Where to read further, and verify.
          </h2>
        </ScrollReveal>
        <div className="mt-14 grid grid-cols-1 gap-x-12 gap-y-10 md:grid-cols-3">
          {REFERENCES.map((r, i) => (
            <ScrollReveal key={r.name} delayMs={80 * (i + 1)}>
              <div className="border-t border-border-strong pt-6">
                <a
                  href={r.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-h3 text-primary underline decoration-border-strong underline-offset-4 transition-colors hover:decoration-primary"
                >
                  {r.name}
                </a>
                <p className="mt-4 text-body text-secondary">{r.note}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
        <ScrollReveal delayMs={320}>
          <p className="mt-16 max-w-2xl text-body-lg text-secondary">
            Most demurrage disputes are resolved in arbitration, not court, and
            most calculations are questioned before they settle. If you want to
            talk one through on real documents,{" "}
            <Link
              href="/contact"
              className="underline decoration-border-strong underline-offset-4 hover:decoration-primary"
            >
              book a working session
            </Link>
            .
          </p>
        </ScrollReveal>
      </Section>
    </main>
  );
}
