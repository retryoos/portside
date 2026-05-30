"use client";

// Claim detail for a single voyage. Driven by the /cases/<id> route: it polls
// the backend (live pipeline -> staged progress -> packet). The reserved id
// "demo" renders the offline lib/demo.ts fixture. Uploading new claims lives
// on /cases.
//
// Rendering model: the full layout (title row + 2-col grid) renders from t=0.
// Each section owns its own skeleton (gated by a `loading` prop) so the page
// never reshapes when stage data lands. The processing stepper sits in a
// grid-rows collapse band at the top; it folds away when stage hits "done"
// (or any negotiation stage). See plans/alright-now-i-want-lucky-adleman.md.
import { useEffect, useState } from "react";
import { pollVoyage } from "@/lib/api";
import { demoVoyage } from "@/lib/demo";
import type { VoyageState } from "@/lib/types";
import AgentSteps from "@/components/AgentSteps";
import BackArrowButton from "@/components/BackArrowButton";
import ClaimLetter from "@/components/ClaimLetter";
import Reveal from "@/components/Reveal";
import SourcesTabs from "@/components/SourcesTabs";

export default function ClaimScreen({ id }: { id?: string }) {
  const voyageId = id && id !== "demo" ? id : null;
  const live = Boolean(voyageId);

  const [voyage, setVoyage] = useState<VoyageState>(demoVoyage);
  const [error, setError] = useState<string | null>(null);

  // Live mode: poll the backend until the pipeline reaches a terminal stage.
  useEffect(() => {
    if (!voyageId) {
      setVoyage(demoVoyage);
      return;
    }
    const controller = new AbortController();
    setError(null);
    pollVoyage(voyageId, setVoyage, {
      signal: controller.signal,
      intervalMs: 2000,
    }).catch((e) => {
      if (controller.signal.aborted) return; // unmount/navigation, not a real error
      setError(e instanceof Error ? e.message : String(e));
    });
    return () => controller.abort();
  }, [voyageId]);

  const cp = voyage.extraction?.charter_party;
  const title = cp
    ? `${cp.vessel_name}, ${cp.load_port} / ${cp.discharge_port}`
    : "Processing voyage…";

  // Per-section readiness. In demo mode every field on `demoVoyage` is
  // populated, so all flags are true and no skeletons render.
  const readyExtraction = Boolean(voyage.extraction);
  const readyPacket = Boolean(voyage.packet);

  // The processing band is open while the pipeline runs (any stage that isn't
  // `done` or a negotiation lifecycle stage). `error` also keeps it open so
  // AgentSteps can show its internal danger banner.
  const processing =
    live &&
    !readyPacket &&
    voyage.stage !== "pending" &&
    voyage.stage !== "rejected" &&
    voyage.stage !== "settled";

  return (
    <main className="mx-auto max-w-[1200px] px-8 py-10">
      {error && (
        <p className="mb-6 rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
          {error}
        </p>
      )}

      {/* Processing band: grid-rows collapse + opacity fade out when done.
          The `0fr -> 1fr` interpolation requires `min-h-0` on the inner
          child so the row track can actually go to zero. */}
      <div
        className={`grid overflow-hidden transition-[grid-template-rows,opacity,margin] duration-500 ease-out ${
          processing ? "grid-rows-[1fr] opacity-100 mb-8" : "grid-rows-[0fr] opacity-0 mb-0"
        }`}
        aria-hidden={!processing}
      >
        <div className="min-h-0">
          {live && <AgentSteps stage={voyage.stage} error={voyage.error} />}
        </div>
      </div>

      {/* Title row: back button on the left, title centred. The title text
          crossfades into place once extraction lands; the row itself is always
          present so nothing shifts. */}
      <div className="relative flex items-center justify-center gap-3">
        <div className="absolute left-0">
          <BackArrowButton href="/cases" />
        </div>
        <div className="min-h-[2.25rem] flex items-center">
          {readyExtraction ? (
            <Reveal ready>
              <h1 className="text-center text-h1 text-primary">{title}</h1>
            </Reveal>
          ) : (
            <div className="h-7 w-72 rounded animate-shimmer" />
          )}
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-[58fr_42fr]">
        <div>
          <ClaimLetter packet={voyage.packet} loading={!readyPacket} />
        </div>
        <div>
          <SourcesTabs voyage={voyage} />
        </div>
      </div>
    </main>
  );
}
