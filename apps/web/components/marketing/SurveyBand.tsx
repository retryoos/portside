import Section from "./Section";
import ScrollReveal from "./ScrollReveal";

// Research band linking to the anonymous AI-adoption survey served at /survey
// (Roman's static site, copied into public/survey and exposed via a rewrite).
//
// The link is a plain <a>, not next/link: /survey is a static document outside
// the Next route tree, so it needs a full-document navigation, not a client RSC
// fetch (which would 404).
export default function SurveyBand() {
  return (
    <Section id="survey" tone="neutral">
      <ScrollReveal>
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between md:gap-16">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Research</p>
            <h2 className="text-display mt-6 text-primary">
              We're studying how maritime really uses AI agents.
            </h2>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              An anonymous, five-minute survey on AI adoption across the
              industry. The results shape what we build next, and we'll publish
              them.
            </p>
          </div>
          <div className="shrink-0">
            <a
              href="/survey"
              className="btn-lift inline-flex rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
            >
              Take the survey
            </a>
          </div>
        </div>
      </ScrollReveal>
    </Section>
  );
}
