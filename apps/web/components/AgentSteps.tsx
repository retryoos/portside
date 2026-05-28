// Live pipeline progress (notes/02-architecture.md §2). Driven off the polled
// VoyageState.stage. Steps before the current one read as done, the current one
// pulses, later ones are muted. The terminal "done" fills every step; "error"
// shows a danger banner instead.
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
      <div className="rounded-md bg-danger-container px-4 py-3 text-body-sm text-danger">
        Pipeline error{error ? `: ${error}` : "."} Please retry the upload.
      </div>
    );
  }

  const current = ORDER.indexOf(stage);

  return (
    <ol className="flex flex-wrap items-center gap-x-2 gap-y-3" aria-label="Pipeline progress">
      {STEPS.map((step) => {
        const idx = ORDER.indexOf(step.stage);
        const done = idx < current;
        const active = idx === current;
        return (
          <li key={step.stage} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`inline-block h-2 w-2 rounded-sm ${
                done || active ? "bg-accent" : "bg-border"
              } ${active ? "animate-pulse" : ""}`}
            />
            <span
              className={`text-label-caps ${
                done || active ? "text-primary" : "text-secondary"
              }`}
            >
              {step.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
