"use client";

// SCREEN: Vessel detail. The vessel has no dedicated endpoint: we fetch the full
// voyage list and filter client-side by vessel_name (route param is
// encodeURIComponent'd, decoded here). Header shows the vessel's aggregates;
// the voyage list reuses the shared <CasesTable/>.
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import CasesTable from "@/components/CasesTable";
import StageChip from "@/components/StageChip";
import { listVoyages } from "@/lib/api";
import type { VoyageSummary } from "@/lib/types";
import { formatEur, formatDate } from "@/lib/format";

export default function VesselDetailPage() {
  const params = useParams<{ name: string }>();
  const name = useMemo(() => {
    const raw = params?.name;
    const value = Array.isArray(raw) ? raw[0] : raw;
    try {
      return value ? decodeURIComponent(value) : "";
    } catch {
      return value ?? "";
    }
  }, [params]);

  const [voyages, setVoyages] = useState<VoyageSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    listVoyages()
      .then((all) => active && setVoyages(all.filter((v) => v.vessel_name === name)))
      .catch((e) => active && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      active = false;
    };
  }, [name]);

  const aggregates = useMemo(() => {
    if (!voyages || voyages.length === 0) return null;
    const quantums = voyages
      .map((v) => v.quantum_eur)
      .filter((q): q is number => q != null);
    const perspectives = Array.from(new Set(voyages.map((v) => v.perspective))).sort();
    return {
      count: voyages.length,
      total: quantums.length ? quantums.reduce((a, b) => a + b, 0) : null,
      latestStage: voyages[0].stage,
      lastActivity: voyages[0].created_at,
      perspectives,
    };
  }, [voyages]);

  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Vessels", name || "Vessel"]} />
      <main className="mx-auto max-w-[1100px] px-6 py-10 md:px-8">
        {error && (
          <p className="rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
            {error}
          </p>
        )}

        {voyages === null && !error && (
          <div className="h-8 w-64 animate-pulse rounded-full bg-surface-muted" aria-busy="true" />
        )}

        {voyages !== null && voyages.length === 0 && !error && (
          <div className="rounded-xl border border-border bg-surface px-6 py-16 text-center">
            <p className="text-h2 text-primary">No claims for {name || "this vessel"}</p>
            <p className="mt-2 text-body-sm text-secondary">
              This vessel has no voyage on file yet.
            </p>
          </div>
        )}

        {aggregates && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-h1 text-primary">{name}</h1>
                  <StageChip stage={aggregates.latestStage} />
                </div>
                <p className="mt-1 text-body-sm capitalize text-secondary">
                  {aggregates.perspectives.join(", ")}
                </p>
              </div>
              <dl className="flex flex-wrap items-baseline gap-x-8 gap-y-2">
                <div className="text-right">
                  <dt className="text-label-caps text-secondary">Claims</dt>
                  <dd className="mt-0.5 text-body tabular-nums text-primary">
                    {aggregates.count}
                  </dd>
                </div>
                <div className="text-right">
                  <dt className="text-label-caps text-secondary">Total quantum</dt>
                  <dd className="mt-0.5 text-body tabular-nums text-primary">
                    {aggregates.total != null ? formatEur(aggregates.total) : "Pending"}
                  </dd>
                </div>
                <div className="text-right">
                  <dt className="text-label-caps text-secondary">Last activity</dt>
                  <dd className="mt-0.5 text-body-sm tabular-nums text-secondary">
                    {formatDate(aggregates.lastActivity)}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="mt-8">
              <CasesTable voyages={voyages ?? []} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
