import type { Metadata } from "next";
import Hero from "@/components/marketing/Hero";
import Section from "@/components/marketing/Section";
import Container from "@/components/marketing/Container";
import ScrollReveal from "@/components/marketing/ScrollReveal";
import LoopVideo from "@/components/marketing/LoopVideo";
import PipelineDiagram from "@/components/marketing/PipelineDiagram";
import CTASection from "@/components/marketing/CTASection";
import Link from "next/link";

// SEO metadata for the landing surface. Open Graph carries the hero
// photograph (with the deep-ink fallback if the asset is missing).
export const metadata: Metadata = {
  title: "Papership.Ai · Recover the demurrage you're owed",
  description:
    "AI workflows for maritime claims. Three voyage documents in. A finished, cited demurrage claim out, in under a minute.",
  openGraph: {
    title: "Papership.Ai · Recover the demurrage you're owed",
    description:
      "AI workflows for maritime claims. Three voyage documents in. A finished, cited demurrage claim out, in under a minute.",
    url: "https://papership.ai/",
    siteName: "Papership.Ai",
    images: ["/photography/hero-landing.jpg"],
    locale: "en_GB",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Papership.Ai",
    description:
      "Three voyage documents in. A finished, cited demurrage claim out, in under a minute.",
    images: ["/photography/hero-landing.jpg"],
  },
};

const TRUST_POINTS = [
  {
    eyebrow: "Citations",
    title: "Every figure traces to its source.",
    body: "Each line in the claim references the contract clause and the port-log event it came from. A reviewer can audit any number in seconds.",
  },
  {
    eyebrow: "Deterministic math",
    title: "The arithmetic is plain code.",
    body: "Laytime is summed by a Python function, not the model. The number on screen is reproducible and locked by a test.",
  },
  {
    eyebrow: "Time bars",
    title: "The 90-day deadline, tracked.",
    body: "Every claim surfaces the contractual time bar so a valid case never expires on a forgotten calendar.",
  },
];

const PRICING_TIERS = [
  {
    name: "Operator",
    audience: "Single-ship operators and small fleets",
    bullets: [
      "Unlimited voyages, one workspace",
      "Edit with AI and PDF export",
      "Email support",
    ],
    cta: "Start a trial",
    href: "/contact",
    accent: false,
  },
  {
    name: "Partner",
    audience: "Claims lawyers and maritime advisors",
    bullets: [
      "Multi-client workspaces",
      "Both sides of the deal (defence + claim)",
      "Priority support",
    ],
    cta: "Talk to us",
    href: "/contact",
    accent: true,
  },
  {
    name: "Enterprise",
    audience: "Large owners, charterers, and brokers",
    bullets: [
      "SSO, audit log, custom retention",
      "Research agents with external data",
      "Dedicated account engineer",
    ],
    cta: "Contact sales",
    href: "/contact",
    accent: false,
  },
];

export default function LandingPage() {
  return (
    <>
      <Hero />

      {/* Section 2 - Problem */}
      <Section id="problem">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Today</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            A ship waits too long. The owner is owed money. Claiming it takes
            days, by hand.
          </h2>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-10 md:grid-cols-3 md:gap-12">
          <ScrollReveal delayMs={80}>
            <p className="text-eyebrow text-secondary">Three documents</p>
            <p className="mt-4 text-body-lg text-secondary">
              The contract, the arrival notice, and the hour-by-hour port log,
              reconciled by hand against each other and against the law.
            </p>
          </ScrollReveal>
          <ScrollReveal delayMs={160}>
            <p className="text-eyebrow text-secondary">Days of expert work</p>
            <p className="mt-4 text-body-lg text-secondary">
              Specialists spend two to four days per voyage. The tools are
              spreadsheets and costly consultants.
            </p>
          </ScrollReveal>
          <ScrollReveal delayMs={240}>
            <p className="text-eyebrow text-secondary">Lost claims</p>
            <p className="mt-4 text-body-lg text-secondary">
              Many valid claims expire past their contractual deadline. That
              money is simply lost.
            </p>
          </ScrollReveal>
        </div>
      </Section>

      {/* Section 3 - Product showcase */}
      <Section id="product" tone="inverse">
        <ScrollReveal>
          <p className="text-eyebrow text-on-primary/70">How it looks</p>
          <h2 className="text-display mt-6 max-w-4xl text-on-primary">
            Three documents in. A finished claim out. In under a minute.
          </h2>
        </ScrollReveal>
        <div className="mt-20 grid grid-cols-1 gap-12 md:grid-cols-3">
          <ScrollReveal delayMs={80}>
            <LoopVideo
              poster="/showcase/upload.jpg"
              caption="Drag and drop the three voyage documents. A new case lands on the dashboard."
            />
          </ScrollReveal>
          <ScrollReveal delayMs={160}>
            <LoopVideo
              poster="/showcase/process.jpg"
              caption="Watch four AI agents hand work to each other, then the EUR 84,375.00 quantum land."
            />
          </ScrollReveal>
          <ScrollReveal delayMs={240}>
            <LoopVideo
              poster="/showcase/edit.jpg"
              caption="Highlight a sentence, refine it with AI, export the cited claim as a PDF."
            />
          </ScrollReveal>
        </div>
      </Section>

      {/* Section 4 - How it works */}
      <Section id="how">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Under the hood</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Four agents. One pipeline. Every figure cited.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            A small fleet of specialised agents reads the documents, calculates
            the laytime, builds the legal argument, and drafts the letter. The
            math is in plain code; the arguments are cited line by line.
          </p>
        </ScrollReveal>
        <div className="mt-16">
          <ScrollReveal delayMs={80}>
            <PipelineDiagram />
          </ScrollReveal>
        </div>
      </Section>

      {/* Section 5 - Trust */}
      <Section id="trust" tone="muted">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Trust</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Numbers a court can audit. Arguments a charterer cannot dismiss.
          </h2>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {TRUST_POINTS.map((point, i) => (
            <ScrollReveal key={point.eyebrow} delayMs={80 * (i + 1)}>
              <div className="h-full rounded-card border border-border bg-surface p-7">
                <p className="text-eyebrow text-secondary">{point.eyebrow}</p>
                <p className="mt-5 text-h2 text-primary">{point.title}</p>
                <p className="mt-4 text-body text-secondary">{point.body}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </Section>

      {/* Section 7 - Pricing */}
      <Section id="pricing">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Pricing</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Pay for what you recover.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            Subscriptions for teams that file claims week in, week out, and a
            success-fee track for those who only want to pay on a win. Final
            numbers land with the first customer.
          </p>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {PRICING_TIERS.map((tier, i) => (
            <ScrollReveal key={tier.name} delayMs={80 * (i + 1)}>
              <div
                className={`flex h-full flex-col rounded-card border p-8 ${
                  tier.accent
                    ? "border-primary bg-primary text-on-primary"
                    : "border-border bg-surface text-primary"
                }`}
              >
                <p
                  className={`text-eyebrow ${
                    tier.accent ? "text-on-primary/70" : "text-secondary"
                  }`}
                >
                  {tier.name}
                </p>
                <p
                  className={`mt-5 text-h2 ${
                    tier.accent ? "text-on-primary" : "text-primary"
                  }`}
                >
                  {tier.audience}
                </p>
                <ul
                  className={`mt-6 flex-1 space-y-3 text-body ${
                    tier.accent ? "text-on-primary/85" : "text-secondary"
                  }`}
                >
                  {tier.bullets.map((b) => (
                    <li key={b} className="flex items-start gap-3">
                      <span
                        aria-hidden
                        className={`mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${
                          tier.accent ? "bg-on-primary/70" : "bg-primary/60"
                        }`}
                      />
                      {b}
                    </li>
                  ))}
                </ul>
                <Link
                  href={tier.href}
                  className={`btn-lift mt-10 rounded-pill px-5 py-3 text-center text-body-sm font-semibold ${
                    tier.accent
                      ? "bg-cta-inverse text-on-cta-inverse hover:bg-cta-inverse-hover"
                      : "bg-cta text-on-cta hover:bg-cta-hover"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            </ScrollReveal>
          ))}
        </div>
        <div className="mt-12">
          <Container>
            <p className="mx-auto max-w-3xl text-center text-body-sm text-secondary">
              Subscriptions billed annually. The success-fee track is offered
              alongside the partner and enterprise plans on request.
            </p>
          </Container>
        </div>
      </Section>

      <CTASection />
    </>
  );
}
