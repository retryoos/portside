"use client";

// Evidence tab (W3, notes/architecture_weeks_5_to_8.md §1.4). Lazy-fetches
// GET /voyages/{id}/evidence-checklist when activated. Each row shows the
// role chip, the analyst's label, a "Supports..." link that scrolls the
// adjacent claim letter into view, and an attached state (✓ / ✗). Rows
// where attached=false render with amber emphasis so the operator sees what
// still needs to be uploaded or research-gathered.
//
// Fetch is gated by `active` so the tab adds zero network until the user
// opens it. A 404 / 409 from the backend (voyage unknown or analysis not
// yet landed) is treated as a soft empty state, not an error toast.

import { useEffect, useState } from "react";
import { fetchEvidenceChecklist } from "@/lib/api";
import { LETTER_DOM_ID } from "@/components/ClaimLetter";
import Reveal from "@/components/Reveal";
import type { EvidenceChecklist, EvidenceItem, EvidenceRole } from "@/lib/types";

const ROLE_LABEL: Record<EvidenceRole, string> = {
  cp_excerpt: "CP excerpt",
  nor: "NOR",
  sof: "SoF",
  bunker_note: "Bunker",
  port_log: "Port log",
  weather_observation: "Weather",
  agent_correspondence: "Agent email",
  other: "Other",
};

export default function EvidenceChecklistTab({
  voyageId,
  active,
}: {
  voyageId: string;
  active: boolean;
}) {
  const [data, setData] = useState<EvidenceChecklist | null | undefined>(
    undefined,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!active || data !== undefined) return;
    const controller = new AbortController();
    fetchEvidenceChecklist(voyageId, controller.signal)
      .then((result) => setData(result))
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      });
    return () => controller.abort();
  }, [active, voyageId, data]);

  if (error) {
    return (
      <p
        role="alert"
        className="rounded-card border border-danger/20 bg-danger-container px-4 py-3 text-body-sm text-danger"
      >
        Could not load evidence checklist: {error}
      </p>
    );
  }

  if (data === undefined) {
    return <EvidenceSkeleton />;
  }

  if (data === null || data.items.length === 0) {
    return (
      <p className="rounded-card border border-border bg-surface-muted px-4 py-6 text-center text-body-sm text-secondary">
        No evidence required yet. The checklist populates once the dispute
        analysis is ready.
      </p>
    );
  }

  const missingCount = data.items.filter((item) => !item.attached).length;

  return (
    <Reveal ready>
      <div>
        <header className="mb-4 flex items-baseline justify-between">
          <p className="text-eyebrow text-secondary">Checklist</p>
          {missingCount > 0 ? (
            <p className="text-body-sm text-warning">
              {missingCount} missing
            </p>
          ) : (
            <p className="text-body-sm text-success">All attached</p>
          )}
        </header>
        <ul className="divide-y divide-border">
          {data.items.map((item, i) => (
            <li key={`${item.role}-${item.label}-${i}`} className="py-3">
              <EvidenceRow item={item} />
            </li>
          ))}
        </ul>
      </div>
    </Reveal>
  );
}

function EvidenceRow({ item }: { item: EvidenceItem }) {
  const attached = item.attached;
  return (
    <div className="flex items-start gap-3">
      <span
        aria-hidden
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
          attached
            ? "bg-success-container text-success"
            : "bg-warning-container text-warning"
        }`}
      >
        {attached ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3 w-3"
          >
            <path d="m5 12 4 4 10-10" />
          </svg>
        ) : (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            className="h-3 w-3"
          >
            <path d="M12 8v5M12 17h.01" />
          </svg>
        )}
      </span>

      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="rounded-pill border border-border bg-surface-muted px-2 py-0.5 text-label-caps text-secondary">
            {ROLE_LABEL[item.role]}
          </span>
          <p
            className={`text-body-sm ${
              attached ? "text-primary" : "text-primary"
            }`}
          >
            {item.label}
          </p>
        </div>
        {(item.supports_event_id || item.supports_clause) && (
          <p className="mt-1">
            <button
              type="button"
              onClick={scrollToLetter}
              className="text-label-caps text-secondary underline-offset-2 transition-colors hover:text-primary hover:underline"
              aria-label="Scroll to letter"
            >
              Supports{" "}
              {[item.supports_clause, item.supports_event_id]
                .filter(Boolean)
                .join(", ")}
            </button>
          </p>
        )}
        {item.note ? (
          <p className="mt-1 text-body-sm text-secondary">{item.note}</p>
        ) : null}
      </div>

      {!attached ? (
        <span className="shrink-0 text-label-caps text-warning">Needed</span>
      ) : null}
    </div>
  );
}

function scrollToLetter() {
  const node = document.getElementById(LETTER_DOM_ID);
  if (!node) return;
  node.scrollIntoView({ block: "start", behavior: "smooth" });
}

function EvidenceSkeleton() {
  return (
    <ul className="divide-y divide-border">
      {[0, 1, 2, 3].map((i) => (
        <li key={i} className="flex items-start gap-3 py-3">
          <div className="mt-0.5 h-5 w-5 shrink-0 rounded-full animate-shimmer" />
          <div className="flex-1 space-y-2">
            <div className="flex gap-2">
              <div className="h-4 w-16 rounded-pill animate-shimmer" />
              <div className="h-3 w-[65%] rounded animate-shimmer" />
            </div>
            <div className="h-3 w-32 rounded animate-shimmer" />
          </div>
        </li>
      ))}
    </ul>
  );
}
