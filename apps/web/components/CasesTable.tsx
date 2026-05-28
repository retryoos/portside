import Link from "next/link";
import type { VoyageSummary } from "@/lib/types";
import { formatEur, formatDate } from "@/lib/format";
import StageChip from "@/components/StageChip";

// Dashboard list of voyage cases (DESIGN.md editorial/legal register). Each row
// links to /cases/<id>; the pipeline stage renders via the shared <StageChip/>.
// Desktop is a five-column ledger; mobile collapses to a scannable stack with
// the quantum and date grouped on a footer line.
export default function CasesTable({ voyages }: { voyages: VoyageSummary[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface">
      <div className="hidden grid-cols-[2.2fr_2fr_1fr_1.2fr_1fr] gap-4 border-b border-border px-5 py-3 text-label-caps text-secondary md:grid">
        <span>Vessel</span>
        <span>Route</span>
        <span>Status</span>
        <span className="text-right">Quantum</span>
        <span className="text-right">Created</span>
      </div>

      <ul>
        {voyages.map((v) => {
          const vessel = v.vessel_name ?? "Processing voyage…";
          const route =
            v.load_port && v.discharge_port
              ? `${v.load_port} / ${v.discharge_port}`
              : "—";
          const quantum =
            v.quantum_eur != null ? formatEur(v.quantum_eur) : "—";
          const created = formatDate(v.created_at);
          return (
            <li key={v.id} className="border-b border-border last:border-b-0">
              <Link
                href={`/cases/${v.id}`}
                className="block transition-colors hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary"
              >
                {/* Desktop ledger row */}
                <div className="hidden grid-cols-[2.2fr_2fr_1fr_1.2fr_1fr] items-center gap-4 px-5 py-4 md:grid">
                  <div>
                    <div className="text-body text-primary">{vessel}</div>
                    <div className="mt-0.5 text-label-caps capitalize text-secondary">
                      {v.perspective}
                    </div>
                  </div>
                  <span className="text-body-sm text-secondary">{route}</span>
                  <span>
                    <StageChip stage={v.stage} />
                  </span>
                  <span className="text-right text-body tabular-nums text-primary">
                    {quantum}
                  </span>
                  <span className="text-right text-body-sm tabular-nums text-secondary">
                    {created}
                  </span>
                </div>

                {/* Mobile stacked card */}
                <div className="px-5 py-4 md:hidden">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-body text-primary">{vessel}</div>
                      <div className="mt-0.5 text-label-caps capitalize text-secondary">
                        {v.perspective}
                      </div>
                    </div>
                    <StageChip stage={v.stage} />
                  </div>
                  <div className="mt-1 text-body-sm text-secondary">{route}</div>
                  <div className="mt-3 flex items-baseline justify-between gap-3">
                    <span className="text-body tabular-nums text-primary">
                      {quantum}
                    </span>
                    <span className="text-body-sm tabular-nums text-secondary">
                      {created}
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
