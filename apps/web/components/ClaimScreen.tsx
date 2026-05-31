"use client";

// Claim detail for a single voyage. Driven by the /cases/<id> route: it polls
// the backend (live pipeline -> staged progress -> packet). The reserved id
// "demo" renders the offline lib/demo.ts fixture. Uploading new claims lives
// on /cases.
//
// Rendering model: the editorial hero (eyebrow + hero-figure quantum + vessel
// subline) renders from t=0 with shape-matched skeletons. Each section owns
// its own skeleton, so the page never reshapes when stage data lands. The
// processing stepper sits in a grid-rows collapse band above the two-column
// layout; it folds away when stage hits "done" (or any negotiation stage).
import { useEffect, useState } from "react";
import { pollVoyage } from "@/lib/api";
import { demoVoyage } from "@/lib/demo";
import { formatEur } from "@/lib/format";
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
      if (controller.signal.aborted) return;
      setError(e instanceof Error ? e.message : String(e));
    });
    return () => controller.abort();
  }, [voyageId]);

  const cp = voyage.extraction?.charter_party;
  const vesselLine = cp
    ? `${cp.vessel_name} · ${cp.load_port} / ${cp.discharge_port}`
    : null;

  const readyExtraction = Boolean(voyage.extraction);
  const readyPacket = Boolean(voyage.packet);

  const processing =
    live &&
    !readyPacket &&
    voyage.stage !== "pending" &&
    voyage.stage !== "rejected" &&
    voyage.stage !== "settled";

  const quantum = voyage.packet?.quantum_eur;
  const quantumStr = quantum != null ? formatEur(quantum) : null;
  const longQuantum = quantumStr ? quantumStr.length > 14 : false;

  return (
    <main className="mx-auto max-w-[1240px] px-6 pb-24 pt-8 md:px-10 md:pt-12">
      <BackArrowButton href="/cases" />

      {error && (
        <p className="mt-6 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger">
          {error}
        </p>
      )}

      {/* Editorial hero. Eyebrow + huge quantum + vessel/route subline. */}
      <header className="mt-10 md:mt-14">
        <p className="text-eyebrow text-secondary">Demurrage due to owners</p>

        <div className="mt-5">
          {quantumStr ? (
            <Reveal ready>
              <p
                className={`text-hero-figure text-primary ${longQuantum ? "text-hero-figure--long" : ""}`}
              >
                {quantumStr}
              </p>
            </Reveal>
          ) : (
            <div className="h-16 w-[28rem] max-w-full rounded animate-shimmer md:h-24" />
          )}
        </div>

        <div className="mt-6 min-h-[1.75rem]">
          {readyExtraction ? (
            <Reveal ready>
              <p className="text-body-lg text-secondary">{vesselLine}</p>
            </Reveal>
          ) : (
            <div className="h-5 w-80 max-w-full rounded animate-shimmer" />
          )}
        </div>
      </header>

      {/* Processing band: grid-rows collapse + opacity fade when done. */}
      <div
        className={`mt-10 grid overflow-hidden transition-[grid-template-rows,opacity,margin] duration-500 ease-out ${
          processing
            ? "grid-rows-[1fr] opacity-100"
            : "mt-0 grid-rows-[0fr] opacity-0"
        }`}
        aria-hidden={!processing}
      >
        <div className="min-h-0">
          {live && <AgentSteps stage={voyage.stage} error={voyage.error} />}
        </div>
      </div>

      <div className="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-[58fr_42fr]">
        <div>
          <ClaimLetter
            packet={voyage.packet}
            loading={!readyPacket}
            voyageId={voyage.voyage_id}
            vesselName={cp?.vessel_name ?? null}
          />
        </div>
        <div>
          <SourcesTabs voyage={voyage} />
        </div>
      </div>
    </main>
  );
}
