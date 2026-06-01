import type { Metadata } from "next";
import Section from "@/components/marketing/Section";
import CTASection from "@/components/marketing/CTASection";

export const metadata: Metadata = {
  title: "About · Laytimely",
  description:
    "Laytimely is an AI-first claims platform for maritime operations, built by Dimitris Kalligaridis and Roman Dolgopolyi at the ACG AI Lab.",
};

// Each founder's photo is a circle crop (rounded-full + object-cover). The
// portrait shot is top-anchored so the face stays in frame; the square shot
// is unaffected by object-position. Files live in /public/founders and are
// served straight through (the middleware matcher excludes dotted paths).
type Founder = {
  name: string;
  role: string;
  image: string;
  /** object-position for the circle crop. */
  imagePosition: string;
  bio: string;
  linkedin?: string;
};

const FOUNDERS: Founder[] = [
  {
    name: "Dimitris Kalligaridis",
    role: "Incoming SDE @ Amazon · AI research at the ACG AI Lab",
    image: "/founders/dimitris.png",
    imagePosition: "object-top",
    bio: "A software engineer focused on distributed systems, optimization, and applied machine learning. He returns to Amazon as an SDE after building backend infrastructure, authorization, and production performance there, and is a 2026 Google Summer of Code contributor at the Eclipse Foundation. At the ACG AI Lab he researches reinforcement-learning agents that make decisions under uncertainty. That same instinct, make the math explicit and let every number trace back to its source, is what powers Laytimely's engine.",
    linkedin: "https://www.linkedin.com/in/dimitrios-kalligaridis",
  },
  {
    name: "Roman Dolgopolyi",
    role: "Explainable AI & cybersecurity researcher · Incoming PhD @ Northeastern",
    image: "/founders/roman.png",
    imagePosition: "object-center",
    bio: "A researcher in Explainable AI and cybersecurity at the ACG AI Lab, and an incoming PhD student at Northeastern University. His published work on explaining AI decisions in cancer-cell diagnosis and his benchmarks for AI safety compliance share one conviction that carries straight into Laytimely: AI trusted with high-stakes decisions has to be transparent and verifiable, never a black box.",
  },
];

export default function AboutPage() {
  return (
    <main className="pt-24">
      <Section>
        <p className="text-eyebrow text-secondary">About us</p>
        <h1 className="text-display mt-6 max-w-3xl text-primary">
          Built by two engineers tired of watching valid claims expire.
        </h1>
        <p className="mt-8 max-w-2xl text-body-lg text-secondary">
          Laytimely is an AI-first claims platform for maritime operations. We
          turn voyage paperwork into a finished, fully cited demurrage claim in
          under a minute, with the arithmetic in plain code rather than the
          model so every figure traces back to the line it came from. Demurrage
          is where we started; the same approach applies anywhere maritime work
          is still done by hand on paper and email.
        </p>
      </Section>

      <Section tone="muted">
        <p className="text-eyebrow text-secondary">Founders</p>
        <h2 className="text-h2 mt-6 max-w-2xl text-primary">
          The people behind Laytimely.
        </h2>

        <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-2">
          {FOUNDERS.map((founder) => (
            <article
              key={founder.name}
              className="rounded-card border border-border bg-surface p-8"
            >
              <div className="flex flex-col items-center gap-6 text-center sm:flex-row sm:items-center sm:text-left">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={founder.image}
                  alt={founder.name}
                  width={112}
                  height={112}
                  className={`h-28 w-28 shrink-0 rounded-full object-cover ring-1 ring-border ${founder.imagePosition}`}
                />
                <div>
                  <h3 className="text-h3 text-primary">{founder.name}</h3>
                  <p className="mt-1 text-body-sm text-secondary">
                    {founder.role}
                  </p>
                </div>
              </div>

              <p className="mt-6 text-body text-secondary">{founder.bio}</p>

              {founder.linkedin ? (
                <a
                  href={founder.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-6 inline-block text-body-sm font-medium text-primary underline underline-offset-4 hover:text-secondary"
                >
                  LinkedIn ↗
                </a>
              ) : null}
            </article>
          ))}
        </div>
      </Section>

      <CTASection />
    </main>
  );
}
