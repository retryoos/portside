"use client";

import { useState } from "react";

// Floating quick-prompt for the inline revise mock. An input pre-filled with
// the demo instruction + a "Refine" CTA. Client-side; no backend.
export default function RevisePrompt({
  defaultValue,
  onRefine,
}: {
  defaultValue: string;
  onRefine?: (instruction: string) => void;
}) {
  const [value, setValue] = useState(defaultValue);

  return (
    <div>
      <p className="text-eyebrow text-secondary">Refine selection</p>
      <div className="mt-3 flex items-center gap-3">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="flex-1 rounded-pill border border-border bg-surface px-5 py-2.5 text-body text-primary outline-none transition-colors focus:border-primary"
          placeholder="How should this be revised?"
        />
        <button
          type="button"
          onClick={() => onRefine?.(value)}
          className="btn-lift shrink-0 rounded-pill bg-cta px-5 py-2.5 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
        >
          Refine
        </button>
      </div>
    </div>
  );
}
