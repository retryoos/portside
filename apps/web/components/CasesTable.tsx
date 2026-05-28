import Link from "next/link";
import type { VoyageSummary } from "@/lib/types";
import { formatEur, formatDate } from "@/lib/format";
import StageChip from "@/components/StageChip";

// Dashboard list of voyage cases (DESIGN.md editorial/legal register). Each row
// links to /cases/<id>; the pipeline stage renders via the shared <StageChip/>.
export default function CasesTable({ voyages }: { voyages: VoyageSummary[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface">
      <div className="hidden grid-cols-[2fr_2fr_1fr_1fr_1fr] gap-4 border-b border-border px-5 py-3 text-label-caps text-secondary md:grid">
        <span>Vessel</span>
        <span>Route</span>
        <span>Status</span>
        <span className="text-right">Quantum</span>
        <span className="text-right">Created</span>
      </div>

      <ul>
        {voyages.map((v) => {
          const route =
            v.load_port && v.discharge_port
              ? `${v.load_port} / ${v.discharge_port}`
              : "—";
          return (
            <li key={v.id} className="border-b border-border last:border-b-0">
              <Link
                href={`/cases/${v.id}`}
                className="grid grid-cols-1 gap-2 px-5 py-4 transition-colors hover:bg-surface-muted md:grid-cols-[2fr_2fr_1fr_1fr_1fr] md:items-center md:gap-4"
              >
                <span className="text-body text-primary">
                  {v.vessel_name ?? "Processing voyage…"}
                  <span className="ml-2 text-body-sm capitalize text-secondary md:hidden">
                    ({v.perspective})
                  </span>
                </span>
                <span className="text-body-sm text-secondary">{route}</span>
                <span>
                  <StageChip stage={v.stage} />
                </span>
                <span className="text-body-sm text-primary md:text-right">
                  {v.quantum_eur != null ? formatEur(v.quantum_eur) : "—"}
                </span>
                <span className="text-body-sm text-secondary md:text-right">
                  {formatDate(v.created_at)}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
