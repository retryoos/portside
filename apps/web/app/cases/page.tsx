"use client";

// SCREEN 0 — Cases dashboard (the app's home; / redirects here). Lists every
// voyage from GET /voyages newest-first, each row linking to /cases/<id>. The
// "New voyage claim" button reveals the shared <Dropzone/> (live upload +
// "Try the demo voyage"); empty and error states are handled inline.
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import CasesTable from "@/components/CasesTable";
import Dropzone from "@/components/Dropzone";
import { createVoyage, listVoyages, type VoyageFiles } from "@/lib/api";
import type { VoyageSummary } from "@/lib/types";

export default function CasesDashboardPage() {
  const router = useRouter();
  const [voyages, setVoyages] = useState<VoyageSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);

  useEffect(() => {
    let active = true;
    listVoyages()
      .then((v) => active && setVoyages(v))
      .catch((e) => active && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = useCallback(
    async (files: VoyageFiles) => {
      setError(null);
      setCreateBusy(true);
      try {
        // Single-perspective product: every claim is filed from the owner's side.
        const id = await createVoyage(files, "owner");
        router.push(`/cases/${id}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setCreateBusy(false);
      }
    },
    [router],
  );

  const handleDemo = useCallback(() => router.push("/cases/demo"), [router]);

  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Voyages", "Cases"]} />
      <main className="mx-auto max-w-[960px] px-8 py-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-primary">Voyage cases</h1>
            <p className="mt-1 text-body-sm text-secondary">
              Every demurrage claim, newest first.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDemo}
              className="rounded-sm px-3.5 py-2.5 text-body-sm text-secondary transition-colors hover:text-primary"
            >
              Try the demo voyage
            </button>
            <button
              type="button"
              onClick={() => setShowUpload((s) => !s)}
              aria-expanded={showUpload}
              className="rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover"
            >
              {showUpload ? "Close" : "New voyage claim"}
            </button>
          </div>
        </div>

        {showUpload && (
          <div className="mt-6">
            <Dropzone onSubmit={handleSubmit} onDemo={handleDemo} busy={createBusy} />
          </div>
        )}

        {error && (
          <p className="mt-6 rounded-md bg-danger-container px-4 py-3 text-body-sm text-danger">
            {error}
          </p>
        )}

        <div className="mt-8">
          {voyages === null && !error && (
            <div
              className="overflow-hidden rounded-md border border-border bg-surface"
              aria-busy="true"
              aria-label="Loading voyages"
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-b-0"
                >
                  <div className="space-y-2">
                    <div className="h-3.5 w-44 animate-pulse rounded-sm bg-surface-muted" />
                    <div className="h-2.5 w-20 animate-pulse rounded-sm bg-surface-muted" />
                  </div>
                  <div className="h-3.5 w-24 animate-pulse rounded-sm bg-surface-muted" />
                </div>
              ))}
            </div>
          )}

          {voyages !== null && voyages.length === 0 && (
            <div className="rounded-md border border-border bg-surface px-6 py-12 text-center">
              <p className="text-body text-primary">No voyage cases yet</p>
              <p className="mt-2 text-body-sm text-secondary">
                Start a new claim from your documents, or try the demo voyage.
              </p>
              <button
                type="button"
                onClick={() => setShowUpload(true)}
                className="mt-5 rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover"
              >
                New voyage claim
              </button>
            </div>
          )}

          {voyages !== null && voyages.length > 0 && <CasesTable voyages={voyages} />}
        </div>
      </main>
    </div>
  );
}
