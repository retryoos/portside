"use client";

// Right-panel tabbed surface (DESIGN.md "Surfaces"): Sources / Calculation /
// Documents, as a pill segmented control. Calculation = LaytimeSummary + SoFTable.
// Documents = supporting docs list. Sources = CP clause excerpts.
//
// Per-tab readiness is derived from `voyage`. While a tab's data has not yet
// landed (pipeline still running), it renders a shape-matched skeleton; the
// real content crossfades in via <Reveal> once available. The Calculation tab
// passes its own readiness down to LaytimeSummary + SoFTable.
import { useState } from "react";
import Reveal from "@/components/Reveal";
import { demoVoyage } from "@/lib/demo";
import EvidenceChecklistTab from "@/components/EvidenceChecklistTab";
import LaytimeSummary from "@/components/LaytimeSummary";
import SoFTable from "@/components/SoFTable";
import type { VoyageState } from "@/lib/types";

type Tab = "sources" | "calculation" | "documents" | "evidence";

const TABS: { id: Tab; label: string }[] = [
  { id: "sources", label: "Sources" },
  { id: "calculation", label: "Calculation" },
  { id: "evidence", label: "Evidence" },
  { id: "documents", label: "Documents" },
];

export default function SourcesTabs({
  voyage = demoVoyage,
}: {
  voyage?: VoyageState;
}) {
  const [active, setActive] = useState<Tab>("calculation");

  const readyClauses = Boolean(voyage.extraction);
  const readyLaytime = Boolean(voyage.laytime);
  const readyDocuments = Boolean(voyage.packet);

  const clauses = voyage.extraction?.charter_party.clause_excerpts ?? [];
  const documents = voyage.packet?.supporting_documents ?? [];

  return (
    <section className="rounded-card border border-border bg-surface p-6">
      <div
        role="tablist"
        aria-label="Claim evidence"
        className="flex gap-1 rounded-pill bg-surface-muted p-1"
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
              className={`flex-1 rounded-pill px-4 py-2 text-label-caps transition-colors ${
                selected
                  ? "bg-primary text-on-primary"
                  : "text-secondary hover:text-primary"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="mt-6">
        {active === "calculation" && (
          <div className="space-y-5">
            <LaytimeSummary laytime={voyage.laytime} loading={!readyLaytime} />
            <SoFTable
              laytime={voyage.laytime}
              flagged={voyage.dispute?.flagged_events ?? []}
              loading={!readyLaytime}
            />
          </div>
        )}

        {active === "sources" &&
          (readyClauses ? (
            <Reveal ready>
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
            </Reveal>
          ) : (
            <ClausesSkeleton />
          ))}

        {active === "evidence" && (
          <EvidenceChecklistTab
            voyageId={voyage.voyage_id}
            active={active === "evidence"}
          />
        )}

        {active === "documents" &&
          (readyDocuments ? (
            <Reveal ready>
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
            </Reveal>
          ) : (
            <DocumentsSkeleton />
          ))}
      </div>
    </section>
  );
}

function ClausesSkeleton() {
  return (
    <ul className="space-y-3">
      {[0, 1, 2].map((i) => (
        <li key={i} className="rounded-lg bg-surface-muted p-4">
          <div className="h-3 w-20 rounded animate-shimmer" />
          <div className="mt-2 space-y-2">
            <div className="h-3 w-full rounded animate-shimmer" />
            <div className="h-3 w-[92%] rounded animate-shimmer" />
            <div className="h-3 w-[70%] rounded animate-shimmer" />
          </div>
        </li>
      ))}
    </ul>
  );
}

function DocumentsSkeleton() {
  return (
    <ul className="divide-y divide-border">
      {[0, 1, 2].map((i) => (
        <li key={i} className="flex items-baseline gap-3 py-3">
          <div className="h-3 w-6 rounded animate-shimmer" />
          <div className="h-3 w-[70%] rounded animate-shimmer" />
        </li>
      ))}
    </ul>
  );
}
