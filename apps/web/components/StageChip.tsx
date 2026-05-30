import type { PipelineStage } from "@/lib/types";

// Status chip for a voyage's claim lifecycle, mapped from the pipeline stage.
// Lifecycle:
//   In progress -> Draft -> Pending -> (Rejected -> back to Draft) -> Settled
// Every chip is a pill with a hairline border (no decorative dots, per
// DESIGN.md), the semantic colour set lives in container/text token pairs.
const STAGE: Record<PipelineStage, { label: string; className: string }> = {
  uploaded: {
    label: "In progress",
    className: "border-warning/30 bg-warning-container text-warning",
  },
  extracting: {
    label: "In progress",
    className: "border-warning/30 bg-warning-container text-warning",
  },
  calculating: {
    label: "In progress",
    className: "border-warning/30 bg-warning-container text-warning",
  },
  analyzing: {
    label: "In progress",
    className: "border-warning/30 bg-warning-container text-warning",
  },
  drafting: {
    label: "In progress",
    className: "border-warning/30 bg-warning-container text-warning",
  },
  done: {
    label: "Draft",
    className: "border-border bg-surface-muted text-primary",
  },
  pending: {
    label: "Pending",
    className: "border-border bg-surface-muted text-primary",
  },
  rejected: {
    label: "Rejected",
    className: "border-danger/30 bg-danger-container text-danger",
  },
  settled: {
    label: "Settled",
    className: "border-success/30 bg-success-container text-success",
  },
  error: {
    label: "Error",
    className: "border-danger/30 bg-danger-container text-danger",
  },
};

export default function StageChip({ stage }: { stage: PipelineStage }) {
  const { label, className } = STAGE[stage];
  return (
    <span
      className={`inline-flex items-center rounded-pill border px-3 py-1 text-label-caps ${className}`}
    >
      {label}
    </span>
  );
}
