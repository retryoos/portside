"use client";

// SCREEN 0: Cases dashboard (the app's home; / redirects here). Lists every
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
    const controller = new AbortController();
    listVoyages(controller.signal)
      .then((v) => setVoyages(v))
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      });
    return () => controller.abort();
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
      <main className="mx-auto max-w-[1100px] px-6 py-10 md:px-8">
        {/* Hero */}
        <section className="relative overflow-hidden rounded-xl border border-border bg-surface px-7 py-9 md:px-10">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-gradient-warm opacity-60 blur-3xl"
          />
          <div className="relative flex flex-wrap items-end justify-between gap-5">
            <div className="max-w-xl">
              <h1 className="text-display text-primary">Voyage cases</h1>
              <p className="mt-3 text-body text-secondary">
                Turn a voyage document bundle into a legally structured demurrage
                claim. Every claim you file lives here, newest first.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleDemo}
                className="rounded-full border border-border bg-surface px-4 py-2.5 text-body-sm font-medium text-primary transition-colors hover:bg-surface-muted"
              >
                Try the demo voyage
              </button>
              <button
                type="button"
                onClick={() => setShowUpload((s) => !s)}
                aria-expanded={showUpload}
                className="rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover"
              >
                {showUpload ? "Close" : "New voyage claim"}
              </button>
            </div>
          </div>
        </section>

        {showUpload && (
          <div className="mt-5">
            <Dropzone onSubmit={handleSubmit} onDemo={handleDemo} busy={createBusy} />
          </div>
        )}

        {error && (
          <p className="mt-5 rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
            {error}
          </p>
        )}

        <div className="mt-6">
          {voyages === null && !error && (
            <div
              className="overflow-hidden rounded-xl border border-border bg-surface"
              aria-busy="true"
              aria-label="Loading voyages"
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

          {voyages !== null && voyages.length === 0 && (
            <div className="relative overflow-hidden rounded-xl border border-border bg-surface px-6 py-16 text-center">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute left-1/2 top-0 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-cool opacity-50 blur-3xl"
              />
              <div className="relative">
                <p className="text-h2 text-primary">No voyage cases yet</p>
                <p className="mx-auto mt-2 max-w-sm text-body-sm text-secondary">
                  Start a new claim from your three voyage documents, or try the
                  demo voyage to see a finished claim end to end.
                </p>
                <button
                  type="button"
                  onClick={() => setShowUpload(true)}
                  className="mt-6 rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover"
                >
                  New voyage claim
                </button>
              </div>
            </div>
          )}

          {voyages !== null && voyages.length > 0 && <CasesTable voyages={voyages} />}
        </div>
      </main>
    </div>
  );
}
