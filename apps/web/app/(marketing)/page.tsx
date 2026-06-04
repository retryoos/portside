import type { Metadata } from "next";
import ReactDOM from "react-dom";
import Hero from "@/components/marketing/Hero";
import Section from "@/components/marketing/Section";
import ScrollReveal from "@/components/marketing/ScrollReveal";
import LoopVideo from "@/components/marketing/LoopVideo";
import PipelineDiagram from "@/components/marketing/PipelineDiagram";
import StudioModel from "@/components/marketing/StudioModel";
import SurveyBand from "@/components/marketing/SurveyBand";
import DemoButton from "@/components/marketing/DemoButton";
import CTASection from "@/components/marketing/CTASection";
import Link from "next/link";

// SEO metadata for the landing surface. The positioning is now company-level:
// an agentic-AI studio for maritime operations, with the demurrage engine as
// the flagship example. OG/Twitter cards reuse the hero photograph.
export const metadata: Metadata = {
  title: "Laytimely, custom AI systems for maritime operations",
  description:
    "We build and embed custom multi-agent AI systems for maritime operational bottlenecks, to scale revenue and cut cost from the bottom up. The demurrage claim engine is one we already shipped.",
  openGraph: {
    title: "Laytimely, custom AI systems for maritime operations",
    description:
      "We build and embed custom multi-agent AI systems for maritime operational bottlenecks. The demurrage claim engine is one we already shipped.",
    url: "https://laytimely.com/",
    siteName: "Laytimely",
    locale: "en_GB",
    type: "website",
    images: ["/photography/hero-landing.jpg"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Laytimely, custom AI systems for maritime operations",
    description:
      "Custom multi-agent AI systems for maritime operations. The demurrage claim engine is one we already shipped.",
    images: ["/photography/hero-landing.jpg"],
  },
};

// The bottlenecks that justify a custom agent: manual work, leaked revenue,
// compounding cost. Maritime-flavoured but framed as the general opportunity.
const BOTTLENECKS = [
  {
    eyebrow: "Manual reconciliation",
    body: "Teams reconcile contracts, port logs, and invoices by hand, line by line. Days of expert time per task, every voyage.",
  },
  {
    eyebrow: "Revenue that leaks",
    body: "Claims expire, demurrage goes unbilled, charter terms go unenforced. Money you are owed, quietly written off.",
  },
  {
    eyebrow: "Cost that compounds",
    body: "Specialists and outside consultants repeat the same judgement calls a tailored agent makes in minutes.",
  },
];

const TRUST_POINTS = [
  {
    eyebrow: "Citations",
    title: "Every figure traces to its source.",
    body: "Each number references the clause and the event it came from. A reviewer can audit any output in seconds.",
  },
  {
    eyebrow: "Deterministic math",
    title: "The arithmetic is plain code.",
    body: "The numbers are summed by a function, not the model. Reproducible, and locked by a test.",
  },
  {
    eyebrow: "Auditable by design",
    title: "Nothing the model asserts goes unchecked.",
    body: "Every step is inspectable: the inputs, the citations, the calculation, the output. A human signs off, not a black box.",
  },
];

// How we engage. Three stages from a fixed-scope pilot to an embedded,
// compounding relationship. No public prices: one route to a real conversation.
const ENGAGEMENT = [
  {
    name: "Pilot",
    audience: "One bottleneck, fixed scope",
    bullets: [
      "We map the workflow and ship a working agent in weeks",
      "Put it in front of your team on your own documents",
      "A fixed price and a clear deliverable, no open-ended retainer",
    ],
    accent: false,
  },
  {
    name: "Build",
    audience: "A production system, embedded",
    bullets: [
      "Tailored to your documents, your terms, your edge cases",
      "Deployed into your stack with citations and an audit trail",
      "Deterministic where it counts, reviewed before it ships",
    ],
    accent: true,
  },
  {
    name: "Embed",
    audience: "An ongoing studio relationship",
    bullets: [
      "More systems, drawn from your growing template library",
      "A forward-deployed engineer who knows your operation",
      "Each agent lands faster and cheaper than the last",
    ],
    accent: false,
  },
];

export default function LandingPage() {
  // Preload the hero photograph at high priority so it paints with the page
  // instead of popping in a beat later. Optimised ~360KB WebP (down from a
  // 3.9MB DSLR JPG); the JPG is retained only for the OG/social preview above,
  // which scrapers fetch out-of-band.
  ReactDOM.preload("/photography/hero-landing.webp", {
    as: "image",
    fetchPriority: "high",
  });
  return (
    <>
      <Hero />

      {/* The opportunity: where manual work, leaked revenue, and cost hide. */}
      <Section id="bottlenecks">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Where the work piles up</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Your operation runs on manual work that software never reached.
            That's where agents pay for themselves.
          </h2>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-10 md:grid-cols-3 md:gap-12">
          {BOTTLENECKS.map((item, i) => (
            <ScrollReveal key={item.eyebrow} delayMs={80 * (i + 1)}>
              <p className="text-eyebrow text-secondary">{item.eyebrow}</p>
              <p className="mt-4 text-body-lg text-secondary">{item.body}</p>
            </ScrollReveal>
          ))}
        </div>
      </Section>

      {/* The studio method: map, build, embed, compound. */}
      <StudioModel />

      {/* Example system 01: the demurrage engine, live today. */}
      <Section id="example" tone="inverse">
        <ScrollReveal>
          <p className="text-eyebrow text-on-primary/70">Example system 01</p>
          <h2 className="text-display mt-6 max-w-4xl text-on-primary">
            Demurrage claims, from three documents to a cited letter in under a
            minute.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-on-primary/80">
            One of our maritime systems, live today. Drop in the contract, the
            arrival notice, and the port log; it calculates the laytime in plain
            code, builds the legal argument with citations, and drafts the claim.
            This is the shape of system we build for your bottleneck.
          </p>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-12 md:grid-cols-3">
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
          <div className="mt-12 flex flex-wrap items-center gap-4">
            <DemoButton className="btn-lift rounded-pill bg-cta-inverse px-6 py-3 text-body-sm font-semibold text-on-cta-inverse hover:bg-cta-inverse-hover disabled:opacity-60" />
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

      {/* Under the hood of that example system. */}
      <Section id="how">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Under the hood</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Four agents. One pipeline. Every figure cited.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            The demurrage system runs a small fleet of specialised agents: one
            reads the documents, one calculates the laytime, one builds the legal
            argument, one drafts the letter. The math is plain code. The
            arguments are cited line by line. Every system we build is shaped
            this way.
          </p>
        </ScrollReveal>
        <div className="mt-16">
          <ScrollReveal delayMs={80}>
            <PipelineDiagram />
          </ScrollReveal>
        </div>
      </Section>

      {/* Why the output holds up. */}
      <Section id="trust" tone="muted">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Why it holds</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Systems a court, or a CFO, can audit.
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

      {/* Research survey (Roman's static site at /survey). */}
      <SurveyBand />

      {/* How we engage: pilot, build, embed. */}
      <Section id="engagement">
        <ScrollReveal>
          <p className="text-eyebrow text-secondary">Engagement</p>
          <h2 className="text-display mt-6 max-w-4xl text-primary">
            Start small. Prove it. Then embed.
          </h2>
          <p className="mt-6 max-w-2xl text-body-lg text-secondary">
            We work in stages, so you see value before you commit. Most teams
            start with a paid pilot on a single bottleneck.
          </p>
        </ScrollReveal>
        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {ENGAGEMENT.map((tier, i) => (
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
              </div>
            </ScrollReveal>
          ))}
        </div>

        {/* Single CTA. No tiered prices: one route to a real conversation. */}
        <ScrollReveal delayMs={320}>
          <div className="mt-16 flex flex-col items-center gap-6 rounded-card border border-border bg-surface px-8 py-12 text-center md:px-12">
            <p className="text-eyebrow text-secondary">Start here</p>
            <h3 className="text-h2 max-w-2xl text-primary">
              Tell us your highest-leverage bottleneck.
            </h3>
            <p className="max-w-xl text-body text-secondary">
              We will map the workflow with you, show you a live agent we already
              built, and scope a pilot. Commercials in private.
            </p>
            <Link
              href="/contact"
              className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
            >
              Book a working session
            </Link>
          </div>
        </ScrollReveal>
      </Section>

      <CTASection />
    </>
  );
}
