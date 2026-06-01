"use client";

// SCREEN: Vessels dashboard. Lists every vessel from GET /vessels (voyages
// grouped by vessel_name), newest activity first, each row linking to the
// filtered detail at /vessels/<encoded name>. Editorial header mirrors
// /cases.
import { useEffect, useState } from "react";
import TopNav from "@/components/TopNav";
import VesselsTable from "@/components/VesselsTable";
import { listVessels } from "@/lib/api";
import type { VesselSummary } from "@/lib/types";

export default function VesselsDashboardPage() {
  const [vessels, setVessels] = useState<VesselSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listVessels(controller.signal)
      .then((v) => setVessels(v))
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        <section className="flex flex-col gap-6 pb-12 pt-8 md:pt-12">
          <p className="text-eyebrow text-secondary">Fleet</p>
          <h1 className="text-hero text-primary">Vessels.</h1>
          <p className="max-w-xl text-body-lg text-secondary">
            Every vessel with a claim on file, most recent activity first.
          </p>
        </section>

        {error && (
          <p className="mb-8 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger">
            {error}
          </p>
        )}

        {vessels === null && !error && (
          <div
            className="overflow-hidden rounded-card border border-border bg-surface"
            aria-busy="true"
            aria-label="Loading vessels"
          >
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="flex items-center justify-between gap-4 border-b border-border px-6 py-5 last:border-b-0"
              >
                <div className="space-y-2">
                  <div className="h-3.5 w-44 animate-pulse rounded-full bg-surface-muted" />
                  <div className="h-2.5 w-20 animate-pulse rounded-full bg-surface-muted" />
                </div>
                <div className="h-3.5 w-24 animate-pulse rounded-full bg-surface-muted" />
              </div>
            ))}
          </div>
        )}

        {vessels !== null && vessels.length === 0 && (
          <div className="rounded-card border border-border bg-surface px-8 py-20 text-center">
            <p className="text-eyebrow text-secondary">Empty fleet</p>
            <h2 className="text-h1 mt-4 text-primary">No vessels yet.</h2>
            <p className="mx-auto mt-4 max-w-md text-body text-secondary">
              Vessels appear here once a voyage claim has been started.
            </p>
          </div>
        )}

        {vessels !== null && vessels.length > 0 && (
          <VesselsTable vessels={vessels} />
        )}
      </main>
    </div>
  );
}
