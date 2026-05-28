// Live pipeline progress (notes/02-architecture.md). Driven off the polled
// VoyageState.stage as a labeled numbered stepper: completed steps show a check,
// the current step is filled with a soft working ring, later ones are muted.
// "error" shows a danger banner instead.
import type { PipelineStage } from "@/lib/types";

const STEPS: { stage: PipelineStage; label: string }[] = [
  { stage: "extracting", label: "Extract documents" },
  { stage: "calculating", label: "Calculate laytime" },
  { stage: "analyzing", label: "Analyse dispute" },
  { stage: "drafting", label: "Draft letter" },
  { stage: "done", label: "Complete" },
];

const ORDER: PipelineStage[] = [
  "uploaded",
  "extracting",
  "calculating",
  "analyzing",
  "drafting",
  "done",
];

export default function AgentSteps({
  stage,
  error,
}: {
  stage: PipelineStage;
  error?: string | null;
}) {
  if (stage === "error") {
    return (
      <div className="rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
        Pipeline error{error ? `: ${error}` : "."} Please retry the upload.
      </div>
    );
  }

  const current = ORDER.indexOf(stage);

  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <p className="text-label-caps text-secondary">Drafting your claim</p>
      <ol
        className="mt-5 flex flex-col gap-0 sm:flex-row sm:items-start sm:gap-0"
        aria-label="Pipeline progress"
      >
        {STEPS.map((step, i) => {
          const idx = ORDER.indexOf(step.stage);
          const done = idx < current;
          const active = idx === current;
          const last = i === STEPS.length - 1;
          return (
            <li
              key={step.stage}
              className="flex items-center gap-3 sm:flex-1 sm:flex-col sm:items-start sm:gap-2"
              aria-current={active ? "step" : undefined}
            >
              <div className="flex items-center gap-3 sm:w-full">
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-body-sm font-semibold ${
                    done
                      ? "bg-primary text-on-primary"
                      : active
                        ? "bg-primary text-on-primary ring-4 ring-accent-container"
                        : "border border-border bg-surface text-secondary"
                  }`}
                >
                  {done ? "✓" : i + 1}
                </span>
                {!last && (
                  <span
                    aria-hidden="true"
                    className={`hidden h-px flex-1 sm:block ${
                      done ? "bg-primary" : "bg-border"
                    }`}
                  />
                )}
              </div>
              <span
                className={`text-body-sm ${
                  done || active ? "font-medium text-primary" : "text-secondary"
                }`}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
