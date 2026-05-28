"use client";

// Right-panel tabbed surface (DESIGN.md "Surfaces"): Sources / Calculation /
// Documents, as a pill segmented control. Calculation = LaytimeSummary + SoFTable.
// Documents = supporting docs list. Sources = CP clause excerpts.
import { useState } from "react";
import { demoVoyage } from "@/lib/demo";
import LaytimeSummary from "@/components/LaytimeSummary";
import SoFTable from "@/components/SoFTable";
import type { VoyageState } from "@/lib/types";

type Tab = "sources" | "calculation" | "documents";

const TABS: { id: Tab; label: string }[] = [
  { id: "sources", label: "Sources" },
  { id: "calculation", label: "Calculation" },
  { id: "documents", label: "Documents" },
];

export default function SourcesTabs({
  voyage = demoVoyage,
}: {
  voyage?: VoyageState;
}) {
  const [active, setActive] = useState<Tab>("calculation");

  const clauses = voyage.extraction?.charter_party.clause_excerpts ?? [];
  const documents = voyage.packet?.supporting_documents ?? [];

  return (
    <section className="rounded-xl border border-border bg-surface p-5">
      <div
        role="tablist"
        aria-label="Claim evidence"
        className="flex gap-1 rounded-full bg-surface-muted p-1"
      >
        {TABS.map((t) => {
          const selected = active === t.id;
          return (
            <button
              key={t.id}
              role="tab"
              type="button"
              aria-selected={selected}
              onClick={() => setActive(t.id)}
              className={`flex-1 rounded-full px-4 py-1.5 text-label-caps transition-colors ${
                selected
                  ? "bg-surface text-primary"
                  : "text-secondary hover:text-primary"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="mt-5">
        {active === "calculation" && (
          <div className="space-y-5">
            <LaytimeSummary laytime={voyage.laytime} />
            <SoFTable
              laytime={voyage.laytime}
              flagged={voyage.dispute?.flagged_events ?? []}
            />
          </div>
        )}

        {active === "sources" && (
          <ul className="space-y-3">
            {clauses.map((c) => (
              <li key={c.clause_no} className="rounded-lg bg-surface-muted p-4">
                <p className="text-label-caps text-secondary">
                  Clause {c.clause_no}
                </p>
                <p className="mt-2 text-letter-body text-primary">{c.text}</p>
              </li>
            ))}
          </ul>
        )}

        {active === "documents" && (
          <ul className="divide-y divide-border">
            {documents.map((doc, i) => (
              <li
                key={`${doc}-${i}`}
                className="flex items-baseline gap-3 py-3 text-body-sm text-primary"
              >
                <span className="text-label-caps tabular-nums text-secondary">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span>{doc}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
