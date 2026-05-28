"use client";

// The SoF / laytime table (DESIGN.md §Screens 2, notes/06-frontend.md §5).
// Columns: TIMESTAMP / DESCRIPTION / CATEGORY / CUM. HRS. Mono ONLY here.
// Numeric column right-aligned. A contestable row is amber-tinted and clickable;
// clicking reveals the matching dispute.flagged_events entry inline. Owner
// position shown as a WORD (Strong/Arguable/Weak), never a percentage.
import { useState } from "react";
import { demoVoyage } from "@/lib/demo";
import {
  confidenceWord,
  formatHours,
  formatLocalTimestamp,
  formatUsd,
} from "@/lib/format";
import type { FlaggedEvent } from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  laytime: "Laytime",
  demurrage: "Demurrage",
  excepted: "Excepted",
};

export default function SoFTable() {
  const lt = demoVoyage.laytime;
  const flagged = demoVoyage.dispute?.flagged_events ?? [];
  const [open, setOpen] = useState<string | null>(null);

  if (!lt) return null;

  const flaggedFor = (eventId: string): FlaggedEvent | undefined =>
    flagged.find((f) => f.event_id === eventId);

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <table className="w-full border-collapse text-mono">
        <thead>
          <tr className="border-b border-border bg-surface-muted">
            <th className="px-3 py-2.5 text-left text-label-caps text-secondary">
              Timestamp
            </th>
            <th className="px-3 py-2.5 text-left text-label-caps text-secondary">
              Description
            </th>
            <th className="px-3 py-2.5 text-left text-label-caps text-secondary">
              Category
            </th>
            <th className="px-3 py-2.5 text-right text-label-caps text-secondary">
              Cum. Hrs
            </th>
          </tr>
        </thead>
        <tbody>
          {lt.rows.map((row, i) => {
            const flag = row.contestable ? flaggedFor(row.event_id_start) : undefined;
            const isOpen = open === row.event_id_start;
            return (
              <RowFragment
                key={`${row.event_id_start}-${i}`}
                contestable={row.contestable}
                isOpen={isOpen}
                onToggle={() =>
                  setOpen(isOpen ? null : row.event_id_start)
                }
                timestamp={formatLocalTimestamp(row.from)}
                description={row.reason}
                category={CATEGORY_LABEL[row.status] ?? row.status}
                cumHrs={formatHours(row.running_total_hours)}
                flag={flag}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RowFragment({
  contestable,
  isOpen,
  onToggle,
  timestamp,
  description,
  category,
  cumHrs,
  flag,
}: {
  contestable: boolean;
  isOpen: boolean;
  onToggle: () => void;
  timestamp: string;
  description: string;
  category: string;
  cumHrs: string;
  flag?: FlaggedEvent;
}) {
  return (
    <>
      <tr
        className={`border-b border-border ${
          contestable
            ? "cursor-pointer border-l-2 border-l-contested bg-contested-container"
            : ""
        }`}
        onClick={contestable ? onToggle : undefined}
        aria-expanded={contestable ? isOpen : undefined}
      >
        <td className="px-3 py-2.5 text-primary">{timestamp}</td>
        <td className="px-3 py-2.5 text-primary">
          {contestable && <span aria-hidden="true">⚑ </span>}
          {description}
        </td>
        <td className="px-3 py-2.5 text-primary">{category}</td>
        <td className="px-3 py-2.5 text-right text-primary tabular-nums">
          {cumHrs}
        </td>
      </tr>
      {contestable && isOpen && flag && (
        <tr className="bg-contested-container">
          <td colSpan={4} className="px-4 pb-4 pt-1">
            <div className="rounded-sm border-l-2 border-l-contested bg-surface p-4">
              <p className="text-h3 text-primary">{flag.title}</p>
              <p className="mt-2 text-body-sm text-secondary">{flag.summary}</p>
              <p className="mt-3 text-body-sm text-primary">
                {flag.owner_argument}
              </p>
              <dl className="mt-4 space-y-1.5">
                <div className="flex items-baseline gap-2">
                  <dt className="text-label-caps text-secondary">
                    Owner position
                  </dt>
                  <dd className="text-body-sm text-primary">
                    {confidenceWord(flag.owner_position_strength)}
                  </dd>
                </div>
                <div className="flex items-baseline gap-2">
                  <dt className="text-label-caps text-secondary">
                    Incremental demurrage
                  </dt>
                  <dd className="text-body-sm text-primary">
                    {formatUsd(flag.incremental_demurrage_usd)}
                  </dd>
                </div>
                <div className="flex items-baseline gap-2">
                  <dt className="text-label-caps text-secondary">Citations</dt>
                  <dd className="text-body-sm text-primary">
                    {flag.clauses_cited.join("; ")}
                  </dd>
                </div>
              </dl>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
