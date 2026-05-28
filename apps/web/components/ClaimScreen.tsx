"use client";

// Claim screen container (notes/15-next-phase.md — Agent 2 live frontend wiring).
// Runs on the LIVE pipeline when an `id` is supplied via the /cases/<id> route
// (pollVoyage feeds each stage in); otherwise it renders the offline lib/demo.ts
// fixture. The leaf components take their data via props, so the same screen
// serves both the live and demo paths. The "demo" id is reserved for the fixture.
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createVoyage, pollVoyage, type VoyageFiles } from "@/lib/api";
import { demoVoyage } from "@/lib/demo";
import type { Perspective, VoyageState } from "@/lib/types";
import ClaimLetter, { LETTER_DOM_ID } from "@/components/ClaimLetter";
import SourcesTabs from "@/components/SourcesTabs";
import TimebarBadge from "@/components/TimebarBadge";
import ExportPdfButton from "@/components/ExportPdfButton";
import AgentSteps from "@/components/AgentSteps";
import Dropzone from "@/components/Dropzone";

export default function ClaimScreen({ id }: { id?: string }) {
  const router = useRouter();
  const voyageId = id && id !== "demo" ? id : null;
  const live = Boolean(voyageId);

  const [voyage, setVoyage] = useState<VoyageState>(demoVoyage);
  const [createBusy, setCreateBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live mode: poll the backend until the pipeline reaches a terminal stage.
  useEffect(() => {
    if (!voyageId) {
      setVoyage(demoVoyage);
      return;
    }
    let active = true;
    setError(null);
    pollVoyage(voyageId, (s) => {
      if (active) setVoyage(s);
    }).catch((e) => {
      if (active) setError(e instanceof Error ? e.message : String(e));
    });
    return () => {
      active = false;
    };
  }, [voyageId]);

  const handleSubmit = useCallback(
    async (files: VoyageFiles, perspective: Perspective) => {
      setError(null);
      setCreateBusy(true);
      try {
        const newId = await createVoyage(files, perspective);
        router.push(`/cases/${newId}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setCreateBusy(false);
      }
    },
    [router],
  );

  const handleDemo = useCallback(() => {
    setError(null);
    setVoyage(demoVoyage);
    router.push("/cases/demo");
  }, [router]);

  const cp = voyage.extraction?.charter_party;
  const title = cp
    ? `${cp.vessel_name} — ${cp.load_port} / ${cp.discharge_port}`
    : live
      ? "Processing voyage…"
      : "MT Aegean Pioneer — Ras Tanura / Rotterdam";

  const hasPacket = Boolean(voyage.packet);
  const showProgress = live && voyage.stage !== "done";

  return (
    <main className="mx-auto max-w-[1200px] px-8 py-10">
      <Dropzone onSubmit={handleSubmit} onDemo={handleDemo} busy={createBusy} />

      {error && (
        <p className="mt-6 rounded-md bg-danger-container px-4 py-3 text-body-sm text-danger">
          {error}
        </p>
      )}

      {showProgress && (
        <div className="mt-8">
          <AgentSteps stage={voyage.stage} error={voyage.error} />
        </div>
      )}

      {hasPacket && (
        <>
          <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="inline-block h-2 w-2 rounded-sm bg-accent" />
              <h1 className="text-h1 text-primary">{title}</h1>
            </div>
            <div className="flex items-center gap-4">
              <TimebarBadge days={voyage.packet?.days_until_time_bar ?? 0} />
              <ExportPdfButton targetId={LETTER_DOM_ID} />
              <button
                type="button"
                className="rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover"
              >
                Send to charterer
              </button>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-[58fr_42fr]">
            <div>
              <ClaimLetter packet={voyage.packet} />
            </div>
            <div>
              <SourcesTabs voyage={voyage} />
            </div>
          </div>
        </>
      )}

      {live && !hasPacket && voyage.stage !== "error" && (
        <p className="mt-8 text-body-sm text-secondary">
          Generating the claim packet from your documents…
        </p>
      )}
    </main>
  );
}
