// Live pipeline progress (notes/02-architecture.md §2). Driven off the polled
// VoyageState.stage. A vertical stepper: completed steps show a check, the active
// step shows a spinning ring, later ones are muted. A thin progress track fills
// as stages advance. "error" shows a danger panel instead. Motion is suppressed
// under prefers-reduced-motion.
import type { PipelineStage } from "@/lib/types";

const STEPS: { stage: PipelineStage; label: string; caption: string }[] = [
  {
    stage: "extracting",
    label: "Extract documents",
    caption: "Reading the charter party, notice of readiness and statement of facts",
  },
  {
    stage: "calculating",
    label: "Calculate laytime",
    caption: "Computing allowed against used laytime and the demurrage due",
  },
  {
    stage: "analyzing",
    label: "Analyse dispute",
    caption: "Weighing the contested events against the charter-party clauses",
  },
  {
    stage: "drafting",
    label: "Draft letter",
    caption: "Composing the claim letter and the dispute narrative",
  },
  { stage: "done", label: "Complete", caption: "The claim packet is ready" },
];

const ORDER: PipelineStage[] = [
  "uploaded",
  "extracting",
  "calculating",
  "analyzing",
  "drafting",
  "done",
];

function Check() {
  return (
    <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="none" aria-hidden="true">
      <path
        d="M5 10.5l3.2 3.2L15 7"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function AgentSteps({
  stage,
  error,
}: {
  stage: PipelineStage;
  error?: string | null;
}) {
  if (stage === "error") {
    return (
      <section className="rounded-md border border-danger-container bg-danger-container px-5 py-4">
        <p className="text-body text-danger">
          We could not process this voyage{error ? `: ${error}` : "."}
        </p>
        <p className="mt-1 text-body-sm text-danger">
          Please retry the upload, or start a new claim.
        </p>
      </section>
    );
  }

  const current = Math.max(ORDER.indexOf(stage), 0);
  const completed = STEPS.filter((s) => ORDER.indexOf(s.stage) < current).length;
  const pct = Math.round((completed / STEPS.length) * 100);

  return (
    <section
      className="rounded-md border border-border bg-surface p-6 sm:p-8"
      aria-label="Processing progress"
      aria-busy="true"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-h2 text-primary">Processing your claim</h2>
        <span className="text-label-caps tabular-nums text-secondary">{pct}%</span>
      </div>
      <p className="mt-2 max-w-[60ch] text-body-sm text-secondary">
        Reading the documents, computing the laytime, and drafting the letter. This
        usually takes 30 to 60 seconds.
      </p>

      <div className="mt-5 h-1 overflow-hidden rounded-sm bg-surface-muted">
        <div
          className="h-full rounded-sm bg-accent transition-[width] duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ol className="mt-7">
        {STEPS.map((step, i) => {
          const idx = ORDER.indexOf(step.stage);
          const done = idx < current;
          const active = idx === current;
          const last = i === STEPS.length - 1;
          return (
            <li key={step.stage} className="grid grid-cols-[auto_1fr] gap-x-4">
              <div className="flex flex-col items-center">
                <span
                  aria-hidden="true"
                  className={
                    done
                      ? "flex h-7 w-7 items-center justify-center rounded-full bg-accent text-on-cta"
                      : active
                        ? "h-7 w-7 animate-spin rounded-full border-2 border-border border-t-accent motion-reduce:animate-none"
                        : "h-7 w-7 rounded-full border-2 border-border"
                  }
                >
                  {done && <Check />}
                </span>
                {!last && (
                  <span
                    aria-hidden="true"
                    className={`my-1 w-px flex-1 ${done ? "bg-accent" : "bg-border"}`}
                  />
                )}
              </div>
              <div className={last ? "pt-0.5" : "pb-6 pt-0.5"}>
                <p className={`text-body ${done || active ? "text-primary" : "text-secondary"}`}>
                  {step.label}
                </p>
                <p
                  className={`mt-0.5 text-body-sm text-secondary ${active ? "animate-pulse motion-reduce:animate-none" : ""}`}
                >
                  {active ? "Working…" : step.caption}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
