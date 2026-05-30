"use client";

import Link from "next/link";
import { useState } from "react";
import type { VoyageSummary } from "@/lib/types";
import { formatEur, formatDate } from "@/lib/format";
import { deleteVoyage } from "@/lib/api";

// Dashboard list of voyage cases. Each row links to /cases/<id>. Desktop is a
// four-column ledger; mobile collapses to a scannable stack with the quantum
// and date on a footer line.
export default function CasesTable({
  voyages,
  onDeleted,
}: {
  voyages: VoyageSummary[];
  onDeleted?: (id: string) => void;
}) {
  const [pendingId, setPendingId] = useState<string | null>(null);

  async function handleDelete(id: string) {
    if (pendingId) return;
    if (!confirm("Delete this claim? This cannot be undone.")) return;
    setPendingId(id);
    try {
      await deleteVoyage(id);
      onDeleted?.(id);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface">
      <div className="hidden grid-cols-[1fr_1fr_1fr_1fr_auto] gap-4 border-b border-border px-5 py-3 text-label-caps text-secondary md:grid">
        <span>Vessel</span>
        <div className="flex justify-center">Route</div>
        <span className="text-right">Quantum</span>
        <span className="text-right">Created</span>
        <span className="w-8" aria-hidden />
      </div>

      <ul>
        {voyages.map((v) => {
          const vessel = v.vessel_name ?? "Processing voyage…";
          const route =
            v.load_port && v.discharge_port
              ? `${v.load_port} / ${v.discharge_port}`
              : "Route pending";
          const quantum =
            v.quantum_eur != null ? formatEur(v.quantum_eur) : "Pending";
          const created = formatDate(v.created_at);
          const isDeleting = pendingId === v.id;
          return (
            <li
              key={v.id}
              className="relative border-b border-border last:border-b-0"
            >
              {/* Desktop ledger row */}
              <div className="hidden grid-cols-[1fr_1fr_1fr_1fr_auto] items-center gap-4 px-5 py-4 transition-colors hover:bg-surface-muted md:grid">
                <Link
                  href={`/cases/${v.id}`}
                  className="contents focus-visible:outline-none"
                  aria-label={`Open claim ${vessel}`}
                >
                  <div>
                    <div className="text-body text-primary">{vessel}</div>
                    <div className="mt-0.5 text-label-caps capitalize text-secondary">
                      {v.perspective}
                    </div>
                  </div>
                  <div className="flex justify-center text-body-sm text-secondary">
                    {route}
                  </div>
                  <span className="text-right text-body tabular-nums text-primary">
                    {quantum}
                  </span>
                  <span className="text-right text-body-sm tabular-nums text-secondary">
                    {created}
                  </span>
                </Link>
                <DeleteButton
                  onClick={() => handleDelete(v.id)}
                  busy={isDeleting}
                />
              </div>

              {/* Mobile stacked card */}
              <div className="px-5 py-4 transition-colors hover:bg-surface-muted md:hidden">
                <div className="flex items-start justify-between gap-3">
                  <Link
                    href={`/cases/${v.id}`}
                    className="min-w-0 flex-1"
                    aria-label={`Open claim ${vessel}`}
                  >
                    <div className="text-body text-primary">{vessel}</div>
                    <div className="mt-0.5 text-label-caps capitalize text-secondary">
                      {v.perspective}
                    </div>
                  </Link>
                  <DeleteButton
                    onClick={() => handleDelete(v.id)}
                    busy={isDeleting}
                  />
                </div>
                <Link href={`/cases/${v.id}`} className="block">
                  <div className="mt-1 text-body-sm text-secondary">{route}</div>
                  <div className="mt-3 flex items-baseline justify-between gap-3">
                    <span className="text-body tabular-nums text-primary">
                      {quantum}
                    </span>
                    <span className="text-body-sm tabular-nums text-secondary">
                      {created}
                    </span>
                  </div>
                </Link>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function DeleteButton({
  onClick,
  busy,
}: {
  onClick: () => void;
  busy: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy}
      aria-label="Delete claim"
      className="flex h-8 w-8 items-center justify-center rounded-full text-secondary transition-colors hover:bg-danger-container hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4"
      >
        <path d="M3 6h18" />
        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
        <path d="M10 11v6" />
        <path d="M14 11v6" />
      </svg>
    </button>
  );
}
