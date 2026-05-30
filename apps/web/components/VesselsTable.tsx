import Link from "next/link";
import type { VesselSummary } from "@/lib/types";
import { formatEur, formatDate } from "@/lib/format";
import StageChip from "@/components/StageChip";

// Dashboard list of vessels. Each row aggregates every voyage that shares a
// vessel_name and links to the filtered detail at /vessels/<encoded name>.
// Mirrors CasesTable: a five-column ledger on desktop, a scannable stack on mobile.
function claimsLabel(n: number): string {
  return n === 1 ? "1 claim" : `${n} claims`;
}

export default function VesselsTable({ vessels }: { vessels: VesselSummary[] }) {
  return (
    <div className="overflow-hidden rounded-card border border-border bg-surface">
      <div className="hidden grid-cols-[2.4fr_1.4fr_7.5rem_1.2fr_1fr] gap-4 border-b border-border bg-surface-muted px-6 py-4 text-label-caps text-secondary md:grid">
        <span>Vessel</span>
        <span>Claims</span>
        <span>Status</span>
        <span className="text-right">Total quantum</span>
        <span className="text-right">Last activity</span>
      </div>

      <ul>
        {vessels.map((v) => {
          const href = `/vessels/${encodeURIComponent(v.name)}`;
          const quantum =
            v.total_quantum_eur != null ? formatEur(v.total_quantum_eur) : "Pending";
          const activity = formatDate(v.last_activity);
          const perspectives = v.perspectives.join(", ");
          return (
            <li key={v.name} className="border-b border-border last:border-b-0">
              <Link
                href={href}
                className="block transition-colors hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary"
              >
                {/* Desktop ledger row */}
                <div className="hidden grid-cols-[2.4fr_1.4fr_7.5rem_1.2fr_1fr] items-center gap-4 px-6 py-5 md:grid">
                  <div>
                    <div className="text-body font-semibold text-primary">
                      {v.name}
                    </div>
                    <div className="mt-1 text-label-caps capitalize text-secondary">
                      {perspectives}
                    </div>
                  </div>
                  <span className="text-body-sm text-secondary">
                    {claimsLabel(v.voyage_count)}
                  </span>
                  <span>
                    <StageChip stage={v.latest_stage} />
                  </span>
                  <span className="text-right text-body tabular-nums text-primary">
                    {quantum}
                  </span>
                  <span className="text-right text-body-sm tabular-nums text-secondary">
                    {activity}
                  </span>
                </div>

                {/* Mobile stacked card */}
                <div className="px-5 py-5 md:hidden">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-body font-semibold text-primary">
                        {v.name}
                      </div>
                      <div className="mt-1 text-label-caps capitalize text-secondary">
                        {perspectives}
                      </div>
                    </div>
                    <StageChip stage={v.latest_stage} />
                  </div>
                  <div className="mt-1 text-body-sm text-secondary">
                    {claimsLabel(v.voyage_count)}
                  </div>
                  <div className="mt-3 flex items-baseline justify-between gap-3">
                    <span className="text-body tabular-nums text-primary">
                      {quantum}
                    </span>
                    <span className="text-body-sm tabular-nums text-secondary">
                      {activity}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
