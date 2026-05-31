"use client";

// The SoF / laytime table (DESIGN.md "Surfaces"). Columns: TIMESTAMP / DESCRIPTION
// / CATEGORY / CUM. HRS. Mono ONLY here, numeric column right-aligned. A
// contestable row is amber-tinted (full tint, no side stripe) and clickable;
// clicking reveals the matching dispute.flagged_events entry inline. Owner
// position shown as a WORD (Strong/Arguable/Weak), never a percentage.
import { useEffect, useState } from "react";
import { fetchClaimStrengths } from "@/lib/api";
import StrengthPanel from "@/components/StrengthPanel";
import { demoVoyage } from "@/lib/demo";
import {
  confidenceWord,
  formatHours,
  formatLocalTimestamp,
  formatEur,
} from "@/lib/format";
import type {
  ClaimStrengthSubScores,
  FlaggedEvent,
  FlaggedEventStrength,
  LaytimeResult,
} from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  laytime: "Laytime",
  demurrage: "Demurrage",
  excepted: "Excepted",
};

export default function SoFTable({
  laytime = demoVoyage.laytime,
  flagged = demoVoyage.dispute?.flagged_events ?? [],
  loading = false,
  voyageId = demoVoyage.voyage_id,
}: {
  laytime?: LaytimeResult | null;
  flagged?: FlaggedEvent[];
  loading?: boolean;
  voyageId?: string;
}) {
  const lt = laytime;
  const [open, setOpen] = useState<string | null>(null);
  // Sub-score panels arrive as a sibling list; fetched once when the dispute
  // lands. Lazy network: no fetch until we actually have flagged events.
  // null === fetched but server returned 404/409 (offline empty); undefined
  // === not yet fetched (skeleton).
  const [strengths, setStrengths] = useState<
    FlaggedEventStrength[] | null | undefined
  >(undefined);

  useEffect(() => {
    if (flagged.length === 0) return;
    const controller = new AbortController();
    fetchClaimStrengths(voyageId, controller.signal)
      .then((rows) => setStrengths(rows))
      .catch(() => setStrengths(null));
    return () => controller.abort();
  }, [voyageId, flagged.length]);

  const subScoresFor = (
    eventId: string,
  ): ClaimStrengthSubScores | undefined => {
    if (!strengths) return undefined;
    return strengths.find((r) => r.event_id === eventId)?.sub_scores;
  };

  const isLoading = loading || !lt;

  const flaggedFor = (eventId: string): FlaggedEvent | undefined =>
    flagged.find((f) => f.event_id === eventId);

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <table className="w-full border-collapse text-mono">
        <thead>
          <tr className="border-b border-border bg-surface-muted">
            <th className="px-3 py-3 text-left text-label-caps text-secondary">
              Timestamp
            </th>
            <th className="px-3 py-3 text-left text-label-caps text-secondary">
              Description
            </th>
            <th className="px-3 py-3 text-left text-label-caps text-secondary">
              Category
            </th>
            <th className="px-3 py-3 text-right text-label-caps text-secondary">
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
                  subScores={flag ? subScoresFor(flag.event_id) : undefined}
                  strengthsReady={strengths !== undefined}
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
  subScores,
  strengthsReady,
}: {
  contestable: boolean;
  isOpen: boolean;
  onToggle: () => void;
  timestamp: string;
  description: string;
  category: string;
  cumHrs: string;
  flag?: FlaggedEvent;
  subScores?: ClaimStrengthSubScores;
  strengthsReady: boolean;
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
              <span className="shrink-0 rounded-pill border border-warning/30 bg-warning-container px-2.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wider text-warning">
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
            <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
              <div className="rounded-md border border-border bg-surface p-5">
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
              {strengthsReady ? (
                <StrengthPanel subScores={subScores} />
              ) : (
                <StrengthPanel subScores={undefined} />
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
