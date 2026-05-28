"use client";

// Claim detail for a single voyage. Driven by the /cases/<id> route: it polls
// the backend (live pipeline -> staged progress -> packet) and then exposes the
// negotiation lifecycle actions (send -> settled | rejected -> revise & resend).
// The reserved id "demo" renders the offline lib/demo.ts fixture read-only (no
// actions, since it is not a real voyage). Uploading new claims lives on /cases.
import { useCallback, useEffect, useState } from "react";
import { pollVoyage, setVoyageStatus } from "@/lib/api";
import { demoVoyage } from "@/lib/demo";
import type { PipelineStage, VoyageState } from "@/lib/types";
import ClaimLetter, { LETTER_DOM_ID } from "@/components/ClaimLetter";
import SourcesTabs from "@/components/SourcesTabs";
import TimebarBadge from "@/components/TimebarBadge";
import ExportPdfButton from "@/components/ExportPdfButton";
import AgentSteps from "@/components/AgentSteps";
import StageChip from "@/components/StageChip";

const PRIMARY =
  "rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover disabled:opacity-50";
const GHOST =
  "rounded-sm px-3.5 py-2.5 text-body-sm text-secondary transition-colors hover:text-primary disabled:opacity-50";

function StageActions({
  stage,
  busy,
  onTransition,
}: {
  stage: PipelineStage;
  busy: boolean;
  onTransition: (next: PipelineStage) => void;
}) {
  if (stage === "done") {
    return (
      <button type="button" disabled={busy} onClick={() => onTransition("pending")} className={PRIMARY}>
        Send to charterer
      </button>
    );
  }
  if (stage === "pending") {
    return (
      <>
        <button type="button" disabled={busy} onClick={() => onTransition("rejected")} className={GHOST}>
          Charterer rejected
        </button>
        <button type="button" disabled={busy} onClick={() => onTransition("settled")} className={PRIMARY}>
          Mark as settled
        </button>
      </>
    );
  }
  if (stage === "rejected") {
    return (
      <button type="button" disabled={busy} onClick={() => onTransition("pending")} className={PRIMARY}>
        Revise &amp; resend
      </button>
    );
  }
  return null;
}

export default function ClaimScreen({ id }: { id?: string }) {
  const voyageId = id && id !== "demo" ? id : null;
  const live = Boolean(voyageId);

  const [voyage, setVoyage] = useState<VoyageState>(demoVoyage);
  const [actionBusy, setActionBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live mode: poll the backend until the pipeline reaches a terminal stage.
  useEffect(() => {
    if (!voyageId) {
      setVoyage(demoVoyage);
      return;
    }
    const controller = new AbortController();
    setError(null);
    pollVoyage(voyageId, setVoyage, { signal: controller.signal }).catch((e) => {
      if (controller.signal.aborted) return; // unmount/navigation, not a real error
      setError(e instanceof Error ? e.message : String(e));
    });
    return () => controller.abort();
  }, [voyageId]);

  const handleTransition = useCallback(
    async (next: PipelineStage) => {
      if (!voyageId) return;
      setError(null);
      setActionBusy(true);
      try {
        setVoyage(await setVoyageStatus(voyageId, next));
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setActionBusy(false);
      }
    },
    [voyageId],
  );

  const cp = voyage.extraction?.charter_party;
  const title = cp
    ? `${cp.vessel_name} — ${cp.load_port} / ${cp.discharge_port}`
    : live
      ? "Processing voyage…"
      : "MT Aegean Pioneer — Ras Tanura / Rotterdam";

  const hasPacket = Boolean(voyage.packet);
  const showProgress = live && !hasPacket;

  return (
    <main className="mx-auto max-w-[1200px] px-8 py-10">
      {error && (
        <p className="mb-6 rounded-md bg-danger-container px-4 py-3 text-body-sm text-danger">
          {error}
        </p>
      )}

      {showProgress && <AgentSteps stage={voyage.stage} error={voyage.error} />}

      {hasPacket && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="inline-block h-2 w-2 rounded-sm bg-accent" />
              <h1 className="text-h1 text-primary">{title}</h1>
              {live && <StageChip stage={voyage.stage} />}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <TimebarBadge days={voyage.packet?.days_until_time_bar ?? 0} />
              <ExportPdfButton targetId={LETTER_DOM_ID} />
              {live && (
                <StageActions stage={voyage.stage} busy={actionBusy} onTransition={handleTransition} />
              )}
            </div>
          </div>

          {live && voyage.stage === "rejected" && (
            <p className="mt-4 rounded-md bg-danger-container px-4 py-3 text-body-sm text-danger">
              The charterer rejected this claim. Revise the letter, then resend to reopen negotiation.
            </p>
          )}

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
    </main>
  );
}
