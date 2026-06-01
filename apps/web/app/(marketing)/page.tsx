import type { Metadata } from "next";
import ReactDOM from "react-dom";
import Hero from "@/components/marketing/Hero";
import Section from "@/components/marketing/Section";
import ScrollReveal from "@/components/marketing/ScrollReveal";
import LoopVideo from "@/components/marketing/LoopVideo";
import PipelineDiagram from "@/components/marketing/PipelineDiagram";
import CTASection from "@/components/marketing/CTASection";
import Link from "next/link";

// SEO metadata for the landing surface. Open Graph + Twitter cards use the
// hero photograph (/photography/hero-landing.jpg) as the link-preview image;
// the title/description keep the AI-forward positioning.
export const metadata: Metadata = {
  title: "Laytimely, AI workflows for maritime operations",
  description:
    "AI workflows for maritime operations, starting with the demurrage claims that used to take days. Three documents in, a cited claim out, in under a minute.",
  openGraph: {
    title: "Laytimely, AI workflows for maritime operations",
    description:
      "AI workflows for maritime operations, starting with the demurrage claims that used to take days. Three documents in, a cited claim out, in under a minute.",
    url: "https://laytimely.com/",
    siteName: "Laytimely",
    locale: "en_GB",
    type: "website",
    images: ["/photography/hero-landing.jpg"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Laytimely, AI workflows for maritime operations",
    description:
      "AI workflows for maritime operations, starting with the demurrage claims that used to take days.",
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

// Segment cards for the "Built for" section. No prices, no per-card CTAs:
// we are deliberately pre-public-pricing and route every reader to the
// single "Pilot programme" CTA below the grid. The cards exist to tell a
// self-qualifying visitor whether the product fits their workflow.
const SEGMENTS = [
  {
    name: "Operators",
    audience: "Single-ship operators and small fleets",
    bullets: [
      "One workspace for every voyage and every claim",
      "Three documents in, a cited claim out, in under a minute",
      "Edit with AI and export to PDF, Word, or Excel",
    ],
    accent: false,
  },
  {
    name: "Advisors",
    audience: "Claims lawyers and maritime consultants",
    bullets: [
      "Run multiple clients side by side in dedicated workspaces",
      "Build both sides of the dispute (claim and rebuttal)",
      "Hand a cited letter to the partner, ready to file",
    ],
    accent: true,
  },
  {
    name: "Enterprises",
    audience: "Large owners, charterers, and brokers",
    bullets: [
      "Workspace per desk, audit log on every action",
      "SSO, custom retention, dedicated account engineer",
      "Research agents tied to your fleet feeds",
    ],
    accent: false,
  },
];

export default function LandingPage() {
  // Preload the hero photograph at high priority so it paints with the page
  // instead of popping in a beat later.
  ReactDOM.preload("/photography/hero-landing.jpg", {
    as: "image",
    fetchPriority: "high",
  });
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
        <ScrollReveal delayMs={320}>
          <div className="mt-12 text-center">
            <a
              href="/sample-claim-letter.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-lift inline-flex items-center gap-2 rounded-pill border border-on-primary/30 px-5 py-2.5 text-body-sm font-semibold text-on-primary hover:bg-on-primary/10"
            >
              See a finished sample letter (PDF)
            </a>
          </div>
        </ScrollReveal>
      </Section>

      {/* Section 4 - How it works */}
      <Section id="how">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Under the hood</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Four AI agents. One pipeline. Every figure cited.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            A small fleet of specialised agents reads the documents, calculates
            the laytime, builds the legal argument, and drafts the letter. The
            math is in plain code. The arguments are cited line by line.
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

      {/* Section 7 - Built for (three audiences, one CTA) */}
      <Section id="pricing">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Built for</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            One workflow. Three kinds of teams who use it daily.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            From a single-ship operator filing one claim a quarter to a global
            broker's claims desk running hundreds, Laytimely is the same
            pipeline, scaled to the team in front of it.
          </p>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {SEGMENTS.map((segment, i) => (
            <ScrollReveal key={segment.name} delayMs={80 * (i + 1)}>
              <div
                className={`flex h-full flex-col rounded-card border p-8 ${
                  segment.accent
                    ? "border-primary bg-primary text-on-primary"
                    : "border-border bg-surface text-primary"
                }`}
              >
                <p
                  className={`text-eyebrow ${
                    segment.accent ? "text-on-primary/70" : "text-secondary"
                  }`}
                >
                  {segment.name}
                </p>
                <p
                  className={`mt-5 text-h2 ${
                    segment.accent ? "text-on-primary" : "text-primary"
                  }`}
                >
                  {segment.audience}
                </p>
                <ul
                  className={`mt-6 flex-1 space-y-3 text-body ${
                    segment.accent ? "text-on-primary/85" : "text-secondary"
                  }`}
                >
                  {segment.bullets.map((b) => (
                    <li key={b} className="flex items-start gap-3">
                      <span
                        aria-hidden
                        className={`mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${
                          segment.accent ? "bg-on-primary/70" : "bg-primary/60"
                        }`}
                      />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            </ScrollReveal>
          ))}
        </div>

        {/* Single pilot-programme CTA. No tiered prices, one route to a
            real conversation. Frames the lack of public pricing as a
            deliberate pilot-programme posture rather than indecision. */}
        <ScrollReveal delayMs={320}>
          <div className="mt-16 flex flex-col items-center gap-6 rounded-card border border-border bg-surface px-8 py-12 text-center md:px-12">
            <p className="text-eyebrow text-secondary">Pilot programme</p>
            <h3 className="text-h2 max-w-2xl text-primary">
              We're working with a small number of teams before broader release.
            </h3>
            <p className="max-w-xl text-body text-secondary">
              Tell us about your fleet or your claims practice. We will set up
              a workspace, walk you through a live voyage on your own
              documents, and discuss commercials in private.
            </p>
            <Link
              href="/contact"
              className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
            >
              Talk to us
            </Link>
          </div>
        </ScrollReveal>
      </Section>

      <CTASection />
    </>
  );
}
