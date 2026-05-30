"use client";

// SCREEN 0: Cases dashboard (the app's home; / redirects here). Lists every
// voyage from GET /voyages newest-first, each row linking to /cases/<id>. The
// "New voyage claim" button reveals the shared <Dropzone/>. Empty and error
// states render inline.
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
        const id = await createVoyage(files, "owner");
        router.push(`/cases/${id}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setCreateBusy(false);
      }
    },
    [router],
  );

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        {/* Editorial header: eyebrow + hero headline + body + primary CTA.
            No card, no shader, no orb. The headline carries the page. */}
        <section className="flex flex-col gap-10 pb-12 pt-8 md:flex-row md:items-end md:justify-between md:gap-16 md:pt-12">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Demurrage workspace</p>
            <h1 className="text-hero mt-4 text-primary">Voyage cases.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Drop in your three voyage documents and Laytimely drafts a
              cited, defensible demurrage claim in under a minute.
            </p>
          </div>
          <div className="flex shrink-0 items-center">
            <button
              type="button"
              onClick={() => setShowUpload((s) => !s)}
              aria-expanded={showUpload}
              className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
            >
              {showUpload ? "Close upload" : "New voyage claim"}
            </button>
          </div>
        </section>

        {showUpload && (
          <div className="pb-8">
            <Dropzone onSubmit={handleSubmit} busy={createBusy} />
          </div>
        )}

        {error && (
          <p className="mb-8 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger">
            {error}
          </p>
        )}

        {voyages === null && !error && (
          <div
            className="overflow-hidden rounded-card border border-border bg-surface"
            aria-busy="true"
            aria-label="Loading voyages"
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

        {voyages !== null && voyages.length === 0 && (
          <div className="rounded-card border border-border bg-surface px-8 py-20 text-center">
            <p className="text-eyebrow text-secondary">No cases yet</p>
            <h2 className="text-h1 mt-4 text-primary">
              Three documents in. A finished claim out.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-body text-secondary">
              Start a new claim from your three voyage documents, or try the
              demo voyage to see a finished claim end to end.
            </p>
            <button
              type="button"
              onClick={() => setShowUpload(true)}
              className="btn-lift mt-8 rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
            >
              New voyage claim
            </button>
          </div>
        )}

        {voyages !== null && voyages.length > 0 && (
          <CasesTable
            voyages={voyages}
            onDeleted={(id) =>
              setVoyages((prev) => (prev ? prev.filter((v) => v.id !== id) : prev))
            }
          />
        )}
      </main>
    </div>
  );
}
