import Section from "./Section";
import ScrollReveal from "./ScrollReveal";

// "How we work": the studio engagement model, the core of the company-level
// pitch. Four numbered steps (map, build, embed, compound) rendered as an
// editorial sequence rather than icon cards, so it reads as a method, not a
// feature grid. Each step is separated by a full top hairline (never a side
// stripe) and a large quiet ordinal.
const STEPS = [
  {
    n: "01",
    title: "Map",
    body: "We sit with your operation and find where hours and revenue leak. The one bottleneck worth automating first.",
  },
  {
    n: "02",
    title: "Build",
    body: "We design a custom multi-agent system for that workflow. Deterministic where it must be, cited, and auditable end to end.",
  },
  {
    n: "03",
    title: "Embed",
    body: "We deploy it into your stack and tailor it to your documents, your terms, your edge cases. Forward-deployed, not thrown over the wall.",
  },
  {
    n: "04",
    title: "Compound",
    body: "Every system we ship seeds a template library, so your second agent is a fraction of the work of your first.",
  },
];

export default function StudioModel() {
  return (
    <Section id="how-we-work" tone="muted">
      <ScrollReveal>
        <p className="text-eyebrow text-secondary">How we work</p>
        <h2 className="text-display mt-6 max-w-4xl text-primary">
          We find your highest-leverage bottleneck and build the system that
          clears it. Then we stay to run it with you.
        </h2>
      </ScrollReveal>
      <div className="mt-16 grid grid-cols-1 gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step, i) => (
          <ScrollReveal key={step.n} delayMs={80 * (i + 1)}>
            <div className="border-t border-border-strong pt-6">
              <p className="text-h2 font-semibold text-secondary">{step.n}</p>
              <h3 className="mt-5 text-h3 text-primary">{step.title}</h3>
              <p className="mt-3 text-body text-secondary">{step.body}</p>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </Section>
  );
}
