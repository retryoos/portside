"use client";

// Claim-strength sub-score panel (W4, notes/architecture_weeks_5_to_8.md §1.5).
// Four neutral chips, one per axis. No numbers, no percentages: the
// architecture is firm that the recipient gets a credible breakdown of why a
// flag reads as it does, not a score they can argue about.
//
// Words come from the closed Strength literal (Strong / Arguable / Weak),
// which mirrors the backend enum so a runtime addition there flags a typecheck
// failure here. Tone of each word is conveyed by the chip color, not text.

import type { ClaimStrengthSubScores, Strength } from "@/lib/types";

const AXIS_LABEL: Array<{ key: keyof ClaimStrengthSubScores; label: string }> = [
  { key: "clause_clarity", label: "Clause clarity" },
  { key: "evidence_completeness", label: "Evidence" },
  { key: "counterparty_pushback_risk", label: "Pushback risk" },
  { key: "time_bar_risk", label: "Time-bar" },
];

// Color tone per axis is "is this a positive read for the owner?" not the
// literal word. counterparty_pushback_risk inverts: a "Weak" pushback risk
// is good for the owner; a "Strong" pushback risk is bad.
function toneFor(
  axis: keyof ClaimStrengthSubScores,
  word: Strength,
): "positive" | "neutral" | "negative" {
  const goodIsLow = axis === "counterparty_pushback_risk" || axis === "time_bar_risk";
  if (word === "Arguable") return "neutral";
  const isStrong = word === "Strong";
  const positive = goodIsLow ? !isStrong : isStrong;
  return positive ? "positive" : "negative";
}

const TONE_CLASS: Record<"positive" | "neutral" | "negative", string> = {
  positive: "bg-success-container text-success",
  neutral: "bg-surface-muted text-secondary",
  negative: "bg-warning-container text-warning",
};

export default function StrengthPanel({
  subScores,
}: {
  subScores: ClaimStrengthSubScores | undefined;
}) {
  if (!subScores) return <StrengthPanelSkeleton />;
  return (
    <section
      aria-label="Claim strength sub-scores"
      className="rounded-md border border-border bg-surface p-4"
    >
      <p className="text-eyebrow text-secondary">Strength</p>
      <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {AXIS_LABEL.map(({ key, label }) => {
          const word = subScores[key];
          const tone = toneFor(key, word);
          return (
            <div key={key} className="flex flex-col gap-1.5">
              <dt className="text-label-caps text-secondary">{label}</dt>
              <dd>
                <span
                  className={`inline-flex rounded-pill px-2.5 py-1 text-body-sm font-semibold ${TONE_CLASS[tone]}`}
                >
                  {word}
                </span>
              </dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
}

function StrengthPanelSkeleton() {
  return (
    <section
      aria-busy
      aria-label="Loading claim strength sub-scores"
      className="rounded-md border border-border bg-surface p-4"
    >
      <div className="h-3 w-16 rounded animate-shimmer" />
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex flex-col gap-1.5">
            <div className="h-2.5 w-20 rounded animate-shimmer" />
            <div className="h-6 w-16 rounded-pill animate-shimmer" />
          </div>
        ))}
      </div>
    </section>
  );
}
