import type { CaseOutcome } from "@/lib/demo";
import { formatEur } from "@/lib/format";

// Screen 1 Outcome block (DESIGN.md §Screens 1). Label-caps heading; a small
// definition-style table with right-aligned numbers. Recovery % and the early
// time-bar clearance are positive -> text-success.
function Row({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-border py-3 last:border-b-0">
      <span className="text-body text-secondary">{label}</span>
      <span
        className={`text-body tabular-nums ${
          positive ? "text-success" : "text-primary"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

export default function OutcomeTable({ outcome }: { outcome: CaseOutcome }) {
  return (
    <section>
      <h2 className="text-label-caps text-secondary">Outcome</h2>
      <div className="mt-4 rounded-card border border-border bg-surface px-6 py-2">
        <Row label="Original claim" value={formatEur(outcome.original_claim_eur)} />
        <Row label="Settled at" value={formatEur(outcome.settled_eur)} />
        <Row
          label="Recovery"
          value={`${outcome.recovery_pct}%`}
          positive
        />
        <Row
          label="Days to settlement"
          value={`${outcome.days_to_settlement} days`}
        />
        <Row label="Time bar" value={outcome.time_bar_status} positive />
      </div>
    </section>
  );
}
