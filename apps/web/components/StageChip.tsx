import type { PipelineStage } from "@/lib/types";

// Status chip for a voyage's pipeline stage (P4 — dashboard table + case header).
// Maps each PipelineStage to a design-token color and a human label: in-progress
// stages (uploaded through drafting) are amber, done reads as ink (claim ready),
// settled is green (money in), error is red.
const STAGE: Record<PipelineStage, { label: string; className: string }> = {
  uploaded: { label: "Uploaded", className: "bg-warning-container text-warning" },
  extracting: { label: "Extracting", className: "bg-warning-container text-warning" },
  calculating: { label: "Calculating", className: "bg-warning-container text-warning" },
  analyzing: { label: "Analyzing", className: "bg-warning-container text-warning" },
  drafting: { label: "Drafting", className: "bg-warning-container text-warning" },
  done: { label: "Done", className: "bg-surface-muted text-primary" },
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
