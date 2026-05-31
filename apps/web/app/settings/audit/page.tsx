"use client";

// SCREEN: /settings/audit. Workspace-admin view of the last 100 audit events
// for the signed-in actor (W6, notes/architecture_weeks_5_to_8.md §2.2).
// Backend already clamps the limit to [1, 500]; the UI requests 100 by
// default and exposes a "Load more" affordance when the page is full.
//
// No charts, no rollups: this is the operational record an admin reviews
// when a customer asks "what did your system do on this case." The page
// follows the same editorial header pattern as /cases (eyebrow + h1 +
// subline) and mounts the AuditTable below.

import { useCallback, useEffect, useState } from "react";

import TopNav from "@/components/TopNav";
import AuditTable from "@/components/settings/AuditTable";
import { listAuditEvents } from "@/lib/api";
import type { AuditEvent } from "@/lib/types";

const PAGE_SIZE = 100;
const MAX_PAGE_SIZE = 500;

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setBusy(true);
    listAuditEvents(limit, controller.signal)
      .then((rows) => setEvents(rows))
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setBusy(false);
      });
    return () => controller.abort();
  }, [limit]);

  const handleLoadMore = useCallback(() => {
    setLimit((l) => Math.min(MAX_PAGE_SIZE, l + PAGE_SIZE));
  }, []);

  const canLoadMore =
    events !== null && events.length >= limit && limit < MAX_PAGE_SIZE;

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        <section className="flex flex-col gap-10 pb-12 pt-8 md:flex-row md:items-end md:justify-between md:gap-16 md:pt-12">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Settings</p>
            <h1 className="text-hero mt-4 text-primary">Audit log.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Every mutation Laytimely recorded on your workspace, newest
              first. Payloads are redacted to non-sensitive fields.
            </p>
          </div>
        </section>

        {error && (
          <p
            role="alert"
            className="mb-8 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger"
          >
            {error}
          </p>
        )}

        {events === null && !error ? (
          <AuditTableSkeleton />
        ) : (
          <>
            <AuditTable events={events ?? []} />
            {canLoadMore && (
              <div className="mt-6 text-center">
                <button
                  type="button"
                  onClick={handleLoadMore}
                  disabled={busy}
                  className="rounded-pill border border-border bg-surface px-5 py-2 text-body-sm text-primary transition-colors hover:bg-surface-muted disabled:opacity-50"
                >
                  {busy ? "Loading…" : `Load more (up to ${MAX_PAGE_SIZE})`}
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function AuditTableSkeleton() {
  return (
    <div
      aria-busy
      aria-label="Loading audit events"
      className="overflow-hidden rounded-card border border-border bg-surface"
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 border-b border-border px-6 py-5 last:border-b-0"
        >
          <div className="space-y-2">
            <div className="h-3 w-40 rounded animate-shimmer" />
            <div className="h-2.5 w-24 rounded animate-shimmer" />
          </div>
          <div className="h-5 w-28 rounded-pill animate-shimmer" />
          <div className="h-3 w-32 rounded animate-shimmer" />
        </div>
      ))}
    </div>
  );
}
