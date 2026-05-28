"use client";

// SCREEN: Vessels dashboard. Lists every vessel from GET /vessels (voyages
// grouped by vessel_name), newest activity first, each row linking to the
// filtered detail at /vessels/<encoded name>. Loading/empty/error states mirror
// the /cases dashboard.
import { useEffect, useState } from "react";
import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import VesselsTable from "@/components/VesselsTable";
import { listVessels } from "@/lib/api";
import type { VesselSummary } from "@/lib/types";

export default function VesselsDashboardPage() {
  const [vessels, setVessels] = useState<VesselSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    listVessels()
      .then((v) => active && setVessels(v))
      .catch((e) => active && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Vessels"]} />
      <main className="mx-auto max-w-[1100px] px-6 py-10 md:px-8">
        <div>
          <h1 className="text-h1 text-primary">Vessels</h1>
          <p className="mt-2 text-body text-secondary">
            Every vessel with a claim on file, most recent activity first.
          </p>
        </div>

        {error && (
          <p className="mt-6 rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
            {error}
          </p>
        )}

        <div className="mt-8">
          {vessels === null && !error && (
            <div
              className="overflow-hidden rounded-xl border border-border bg-surface"
              aria-busy="true"
              aria-label="Loading vessels"
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-b-0"
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
            <div className="rounded-xl border border-border bg-surface px-6 py-16 text-center">
              <p className="text-h2 text-primary">No vessels yet</p>
              <p className="mx-auto mt-2 max-w-sm text-body-sm text-secondary">
                Vessels appear here once a voyage claim has been started.
              </p>
            </div>
          )}

          {vessels !== null && vessels.length > 0 && (
            <VesselsTable vessels={vessels} />
          )}
        </div>
      </main>
    </div>
  );
}
