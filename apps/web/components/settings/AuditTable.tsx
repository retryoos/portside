"use client";

// Audit log table (W6, notes/architecture_weeks_5_to_8.md §2.2). Renders the
// last N rows returned by GET /audit with two client-side filters (action,
// target_type) and a date-direction toggle. No charts, no rollups: this is
// the workspace's "what got done by whom" record, not a dashboard.
//
// Voyage target ids link to /cases/<id> so an admin can jump from a
// recorded mutation to the live voyage. The redacted payload is rendered
// as a single compact JSON line; clicking the row expands it to a pretty
// printed block so the operator can inspect what got logged.

import Link from "next/link";
import { useMemo, useState } from "react";

import type { AuditEvent } from "@/lib/types";

const ACTION_LABEL: Record<string, string> = {
  "voyage.create": "Voyage created",
  "voyage.delete": "Voyage deleted",
  "voyage.status_change": "Status change",
  "voyage.revise_apply": "Revision applied",
  "voyage.rebuttal": "Rebuttal drafted",
  "voyage.letter_email": "Letter emailed",
  "voyage.evidence_refresh": "Evidence refreshed",
  "voyage.from_email": "From inbound email",
  "workspace.create": "Workspace created",
  "workspace.invite": "Member invited",
  "workspace.accept": "Invite accepted",
  "workspace.member_remove": "Member removed",
};

type SortDir = "desc" | "asc";

export default function AuditTable({ events }: { events: AuditEvent[] }) {
  const [actionFilter, setActionFilter] = useState<string>("");
  const [targetFilter, setTargetFilter] = useState<string>("");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [expanded, setExpanded] = useState<number | null>(null);

  // Build option lists from what's actually in the page so empty actions /
  // targets do not clutter the dropdown.
  const actionOptions = useMemo(
    () => Array.from(new Set(events.map((e) => e.action))).sort(),
    [events],
  );
  const targetOptions = useMemo(
    () => Array.from(new Set(events.map((e) => e.target_type))).sort(),
    [events],
  );

  const filtered = useMemo(() => {
    const rows = events.filter((e) => {
      if (actionFilter && e.action !== actionFilter) return false;
      if (targetFilter && e.target_type !== targetFilter) return false;
      return true;
    });
    return rows.sort((a, b) =>
      sortDir === "desc" ? b.at.localeCompare(a.at) : a.at.localeCompare(b.at),
    );
  }, [events, actionFilter, targetFilter, sortDir]);

  if (events.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface px-8 py-20 text-center">
        <p className="text-eyebrow text-secondary">No audit events</p>
        <h2 className="text-h2 mt-4 text-primary">Nothing logged yet.</h2>
        <p className="mx-auto mt-4 max-w-md text-body text-secondary">
          Audit rows land here as soon as you create, edit, or email a voyage.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <FilterSelect
          label="Action"
          value={actionFilter}
          onChange={setActionFilter}
          options={actionOptions}
          optionLabel={(v) => ACTION_LABEL[v] ?? v}
        />
        <FilterSelect
          label="Target"
          value={targetFilter}
          onChange={setTargetFilter}
          options={targetOptions}
        />
        <button
          type="button"
          onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
          aria-label={`Sort by date ${sortDir === "desc" ? "ascending" : "descending"}`}
          className="ml-auto inline-flex h-9 items-center gap-1.5 rounded-pill border border-border bg-surface px-3 text-body-sm text-primary transition-colors hover:bg-surface-muted"
        >
          Date
          <svg
            aria-hidden
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`h-3.5 w-3.5 transition-transform ${sortDir === "asc" ? "rotate-180" : ""}`}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        <p className="basis-full text-body-sm text-secondary">
          {filtered.length} of {events.length}
        </p>
      </div>

      <div className="overflow-hidden rounded-card border border-border bg-surface">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-label-caps text-secondary">
              <th className="px-4 py-3 text-left">When</th>
              <th className="px-4 py-3 text-left">Actor</th>
              <th className="px-4 py-3 text-left">Action</th>
              <th className="px-4 py-3 text-left">Target</th>
              <th className="px-4 py-3 text-left">Payload</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <AuditRow
                key={e.id}
                event={e}
                expanded={expanded === e.id}
                onToggle={() => setExpanded(expanded === e.id ? null : e.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AuditRow({
  event,
  expanded,
  onToggle,
}: {
  event: AuditEvent;
  expanded: boolean;
  onToggle: () => void;
}) {
  const actionLabel = ACTION_LABEL[event.action] ?? event.action;
  const targetIsVoyage = event.target_type === "voyage";
  const payloadOneLine = useMemo(
    () => formatPayloadOneLine(event.payload),
    [event.payload],
  );
  const payloadPretty = useMemo(
    () => JSON.stringify(event.payload, null, 2),
    [event.payload],
  );

  return (
    <>
      <tr
        className="cursor-pointer border-b border-border transition-colors hover:bg-surface-muted"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <td className="px-4 py-3 align-top text-body-sm tabular-nums text-primary">
          {formatTimestamp(event.at)}
        </td>
        <td className="px-4 py-3 align-top text-body-sm text-primary">
          {event.actor_sub ? truncate(event.actor_sub, 22) : "-"}
        </td>
        <td className="px-4 py-3 align-top">
          <span className="inline-flex rounded-pill border border-border bg-surface-muted px-2.5 py-0.5 text-body-sm text-primary">
            {actionLabel}
          </span>
        </td>
        <td className="px-4 py-3 align-top text-body-sm">
          {targetIsVoyage ? (
            <Link
              href={`/cases/${event.target_id}`}
              onClick={(e) => e.stopPropagation()}
              className="text-primary underline underline-offset-2 hover:text-secondary"
            >
              {truncate(event.target_id, 24)}
            </Link>
          ) : (
            <span className="text-primary">{truncate(event.target_id, 24)}</span>
          )}
          <span className="ml-2 text-label-caps text-secondary">
            {event.target_type}
          </span>
        </td>
        <td className="px-4 py-3 align-top">
          <code className="block max-w-[26ch] truncate font-mono text-body-sm text-secondary">
            {payloadOneLine}
          </code>
        </td>
      </tr>
      {expanded ? (
        <tr className="border-b border-border bg-surface-muted">
          <td colSpan={5} className="px-4 py-3">
            <pre className="overflow-x-auto whitespace-pre-wrap break-words font-mono text-body-sm text-primary">
              {payloadPretty}
            </pre>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
  optionLabel,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  options: string[];
  optionLabel?: (v: string) => string;
}) {
  return (
    <label className="inline-flex items-center gap-2 text-body-sm text-secondary">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-pill border border-border bg-surface px-3 py-1.5 text-body-sm text-primary outline-none transition-colors focus:border-primary"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {optionLabel ? optionLabel(o) : o}
          </option>
        ))}
      </select>
    </label>
  );
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + "…";
}

function formatPayloadOneLine(payload: Record<string, unknown>): string {
  const keys = Object.keys(payload);
  if (keys.length === 0) return "{}";
  return JSON.stringify(payload);
}
