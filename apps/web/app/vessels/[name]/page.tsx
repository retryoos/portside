"use client";

// SCREEN: Vessel detail. The vessel has no dedicated endpoint: we fetch the
// full voyage list and filter client-side by vessel_name. Header is the
// editorial pattern with the vessel name as the hero and a small aggregate
// strip below it.
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import BackArrowButton from "@/components/BackArrowButton";
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
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 pt-8 md:px-8 md:pt-12">
        <BackArrowButton href="/vessels" />

        {error && (
          <p className="mt-6 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger">
            {error}
          </p>
        )}

        {voyages === null && !error && (
          <div
            className="mt-10 h-12 w-72 animate-pulse rounded-pill bg-surface-muted"
            aria-busy="true"
          />
        )}

        {voyages !== null && voyages.length === 0 && !error && (
          <div className="mt-10 rounded-card border border-border bg-surface px-8 py-20 text-center">
            <p className="text-eyebrow text-secondary">No claims yet</p>
            <h2 className="text-h1 mt-4 text-primary">
              {name || "This vessel"} has no voyages on file.
            </h2>
          </div>
        )}

        {aggregates && (
          <>
            <header className="mt-10">
              <p className="text-eyebrow text-secondary">Vessel</p>
              <div className="mt-4 flex flex-wrap items-baseline gap-x-6 gap-y-3">
                <h1 className="text-h1 text-primary md:text-display">{name}</h1>
                <StageChip stage={aggregates.latestStage} />
              </div>
              <p className="mt-3 text-body-lg capitalize text-secondary">
                {aggregates.perspectives.join(", ")}
              </p>

              <dl className="mt-8 grid grid-cols-2 gap-x-8 gap-y-5 border-t border-border pt-6 md:grid-cols-3">
                <div>
                  <dt className="text-eyebrow text-secondary">Claims</dt>
                  <dd className="mt-2 text-h2 tabular-nums text-primary">
                    {aggregates.count}
                  </dd>
                </div>
                <div>
                  <dt className="text-eyebrow text-secondary">Total quantum</dt>
                  <dd className="mt-2 text-h2 tabular-nums text-primary">
                    {aggregates.total != null
                      ? formatEur(aggregates.total)
                      : "Pending"}
                  </dd>
                </div>
                <div>
                  <dt className="text-eyebrow text-secondary">Last activity</dt>
                  <dd className="mt-2 text-h2 tabular-nums text-primary">
                    {formatDate(aggregates.lastActivity)}
                  </dd>
                </div>
              </dl>
            </header>

            <div className="mt-12">
              <CasesTable voyages={voyages ?? []} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
