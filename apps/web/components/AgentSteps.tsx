"use client";

// Live pipeline progress (notes/02-architecture.md). Driven off the polled
// VoyageState.stage as a labeled numbered stepper: completed steps show a check,
// the current step is filled with a soft working ring, later ones are muted.
// "error" shows a danger banner instead.
//
// The connector after the active step trickle-fills (see TRICKLE_CAP) so the
// jump between stages reads as continuous loading rather than a snap. The
// backend reports no per-stage ETA, so the fill is paced off a deliberate
// estimate and parks short of full until the next stage actually arrives.
import { useEffect, useState } from "react";
import type { PipelineStage } from "@/lib/types";

const STEPS: { stage: PipelineStage; label: string }[] = [
  { stage: "extracting", label: "Extract documents" },
  { stage: "calculating", label: "Calculate laytime" },
  { stage: "analyzing", label: "Analyse dispute" },
  { stage: "drafting", label: "Draft letter" },
  { stage: "done", label: "Complete" },
];

const ORDER: PipelineStage[] = [
  "uploaded",
  "extracting",
  "calculating",
  "analyzing",
  "drafting",
  "done",
];

// Rough wall-clock cost of each stage (one LLM call apiece). Used only to pace
// the trickle; faster stages fill faster. Tuned, not measured.
const EXPECTED_MS: Partial<Record<PipelineStage, number>> = {
  extracting: 7000,
  calculating: 5000,
  analyzing: 5000,
  drafting: 9000,
};

// The active connector eases toward this fraction and parks there until the
// next stage arrives, so it never reads as finished before it is.
const TRICKLE_CAP = 0.9;

export default function AgentSteps({
  stage,
  error,
}: {
  stage: PipelineStage;
  error?: string | null;
}) {
  // Tagged with its stage so a stage change reads as 0 fill on the next active
  // connector immediately (before the effect re-fires), avoiding a flash of the
  // previous stage's progress.
  const [trickle, setTrickle] = useState<{ stage: PipelineStage; value: number }>({
    stage,
    value: 0,
  });

  useEffect(() => {
    if (stage === "error") return;
    const start = performance.now();
    const tau = (EXPECTED_MS[stage] ?? 6000) / 1.6;
    setTrickle({ stage, value: 0 });
    const interval = setInterval(() => {
      const elapsed = performance.now() - start;
      setTrickle({
        stage,
        value: Math.min(TRICKLE_CAP, 1 - Math.exp(-elapsed / tau)),
      });
    }, 120);
    return () => clearInterval(interval);
  }, [stage]);

  if (stage === "error") {
    return (
      <div className="rounded-xl bg-danger-container px-4 py-3 text-body-sm text-danger">
        Pipeline error{error ? `: ${error}` : "."} Please retry the upload.
      </div>
    );
  }

  const current = ORDER.indexOf(stage);
  const activeFill = trickle.stage === stage ? trickle.value : 0;

  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <p className="text-label-caps text-secondary">Drafting your claim</p>
      <ol
        className="mt-5 flex flex-col gap-3 sm:grid sm:grid-cols-5 sm:gap-0"
        aria-label="Pipeline progress"
      >
        {STEPS.map((step, i) => {
          const idx = ORDER.indexOf(step.stage);
          const done = idx < current;
          const active = idx === current;
          const last = i === STEPS.length - 1;
          const fill = done ? 1 : active ? activeFill : 0;
          return (
            <li
              key={step.stage}
              className="relative flex items-center gap-3 sm:flex-col sm:items-center sm:gap-2"
              aria-current={active ? "step" : undefined}
            >
              {/* Connector: runs from this circle's right edge to the next
                  circle's left edge. Circle is h-7/w-7 (28px) and sits at the
                  column centre, so the line is anchored at 14px past centre
                  on each side. Hidden on mobile (stacked layout). */}
              {!last && (
                <span
                  aria-hidden="true"
                  className="absolute top-[13px] hidden h-0.5 overflow-hidden bg-border sm:block"
                  style={{
                    left: "calc(50% + 18px)",
                    right: "calc(-50% + 18px)",
                  }}
                >
                  <span
                    className="absolute inset-y-0 left-0 bg-primary transition-[width] duration-150 ease-linear"
                    style={{ width: `${fill * 100}%` }}
                  />
                </span>
              )}

              <span
                className={`relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-body-sm font-semibold ${
                  done
                    ? "bg-primary text-on-primary"
                    : active
                      ? "bg-primary text-on-primary ring-4 ring-accent-container"
                      : "border border-border bg-surface text-secondary"
                }`}
              >
                {done ? "✓" : i + 1}
              </span>

              <span
                className={`text-body-sm sm:text-center ${
                  done || active ? "font-medium text-primary" : "text-secondary"
                }`}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
