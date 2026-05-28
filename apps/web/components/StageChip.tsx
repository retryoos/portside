import type { PipelineStage } from "@/lib/types";

// Status chip for a voyage's claim lifecycle, mapped from the pipeline stage.
// Kept to the few statuses a claims desk actually acts on: In progress (the
// pipeline is still extracting/calculating/drafting) -> Draft (the claim packet
// is drafted and ready to send to the charterer; the pipeline's "done" stage)
// -> Settled (resolved, money in). Error on failure. Colors: amber = working,
// ink = drafted/ready to send, green = settled, red = error.
const STAGE: Record<PipelineStage, { label: string; className: string }> = {
  uploaded: { label: "In progress", className: "bg-warning-container text-warning" },
  extracting: { label: "In progress", className: "bg-warning-container text-warning" },
  calculating: { label: "In progress", className: "bg-warning-container text-warning" },
  analyzing: { label: "In progress", className: "bg-warning-container text-warning" },
  drafting: { label: "In progress", className: "bg-warning-container text-warning" },
  done: { label: "Draft", className: "bg-surface-muted text-primary" },
  settled: { label: "Settled", className: "bg-success-container text-success" },
  error: { label: "Error", className: "bg-danger-container text-danger" },
};

export default function StageChip({ stage }: { stage: PipelineStage }) {
  const { label, className } = STAGE[stage];
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2 py-0.5 text-label-caps uppercase ${className}`}
    >
      {label}
    </span>
  );
}
