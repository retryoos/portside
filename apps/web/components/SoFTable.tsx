"use client";

// The SoF / laytime table (DESIGN.md "Surfaces"). Columns: TIMESTAMP / DESCRIPTION
// / CATEGORY / CUM. HRS. Mono ONLY here, numeric column right-aligned. A
// contestable row is amber-tinted (full tint, no side stripe) and clickable;
// clicking reveals the matching dispute.flagged_events entry inline. Owner
// position shown as a WORD (Strong/Arguable/Weak), never a percentage.
import { useState } from "react";
import Reveal from "@/components/Reveal";
import { demoVoyage } from "@/lib/demo";
import {
  confidenceWord,
  formatHours,
  formatLocalTimestamp,
  formatEur,
} from "@/lib/format";
import type { FlaggedEvent, LaytimeResult } from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  laytime: "Laytime",
  demurrage: "Demurrage",
  excepted: "Excepted",
};

export default function SoFTable({
  laytime = demoVoyage.laytime,
  flagged = demoVoyage.dispute?.flagged_events ?? [],
  loading = false,
}: {
  laytime?: LaytimeResult | null;
  flagged?: FlaggedEvent[];
  loading?: boolean;
}) {
  const lt = laytime;
  const [open, setOpen] = useState<string | null>(null);

  const isLoading = loading || !lt;

  const flaggedFor = (eventId: string): FlaggedEvent | undefined =>
    flagged.find((f) => f.event_id === eventId);

  return (
    <div className="overflow-hidden rounded-lg border border-border">
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
        {isLoading ? (
          <SkeletonBody />
        ) : (
          <tbody>
            {lt!.rows.map((row, i) => {
              const flag = row.contestable
                ? flaggedFor(row.event_id_start)
                : undefined;
              const isOpen = open === row.event_id_start;
              return (
                <RowFragment
                  key={`${row.event_id_start}-${i}`}
                  contestable={row.contestable}
                  isOpen={isOpen}
                  onToggle={() => setOpen(isOpen ? null : row.event_id_start)}
                  timestamp={formatLocalTimestamp(row.from)}
                  description={row.reason}
                  category={CATEGORY_LABEL[row.status] ?? row.status}
                  cumHrs={formatHours(row.running_total_hours)}
                  flag={flag}
                />
              );
            })}
          </tbody>
        )}
      </table>
    </div>
  );
}

// Skeleton tbody: 6 placeholder rows that match the real row geometry. The
// real <thead> above anchors column widths so nothing shifts when bodies swap.
function SkeletonBody() {
  return (
    <tbody>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <tr key={i} className="border-b border-border">
          <td className="px-3 py-2.5 align-top">
            <div className="h-3 w-28 rounded animate-shimmer" />
          </td>
          <td className="px-3 py-2.5 align-top">
            <div className="h-3 w-[80%] rounded animate-shimmer" />
          </td>
          <td className="px-3 py-2.5 align-top">
            <div className="h-3 w-16 rounded animate-shimmer" />
          </td>
          <td className="px-3 py-2.5 align-top">
            <div className="ml-auto h-3 w-10 rounded animate-shimmer" />
          </td>
        </tr>
      ))}
    </tbody>
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
          contestable ? "cursor-pointer bg-contested-container" : ""
        }`}
        onClick={contestable ? onToggle : undefined}
        aria-expanded={contestable ? isOpen : undefined}
      >
        <td className="px-3 py-2.5 align-top text-primary">{timestamp}</td>
        <td className="px-3 py-2.5 align-top text-primary">
          <span className="flex items-start gap-2">
            <span>{description}</span>
            {contestable && (
              <span className="shrink-0 rounded-full bg-contested px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wider text-on-warning">
                Contested
              </span>
            )}
          </span>
        </td>
        <td className="px-3 py-2.5 align-top text-primary">{category}</td>
        <td className="px-3 py-2.5 text-right align-top tabular-nums text-primary">
          {cumHrs}
        </td>
      </tr>
      {contestable && isOpen && flag && (
        <tr className="bg-contested-container">
          <td colSpan={4} className="px-3 pb-4 pt-1">
            <div className="rounded-lg border border-border bg-surface p-4">
              <p className="text-h3 text-primary">{flag.title}</p>
              <p className="mt-2 text-body-sm text-secondary">{flag.summary}</p>
              <p className="mt-3 text-body-sm text-primary">{flag.owner_argument}</p>
              <dl className="mt-4 space-y-1.5">
                <div className="flex items-baseline gap-2">
                  <dt className="text-label-caps text-secondary">Owner position</dt>
                  <dd className="text-body-sm text-primary">
                    {confidenceWord(flag.owner_position_strength)}
                  </dd>
                </div>
                <div className="flex items-baseline gap-2">
                  <dt className="text-label-caps text-secondary">
                    Incremental demurrage
                  </dt>
                  <dd className="text-body-sm tabular-nums text-primary">
                    {formatEur(flag.incremental_demurrage_eur)}
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
