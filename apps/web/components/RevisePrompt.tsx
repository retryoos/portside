"use client";

import { useState } from "react";

// Screen 3 floating quick-prompt (DESIGN.md §Screens 3). Client-side mock: an
// input pre-filled with the demo instruction + a "Refine" action. No backend.
export default function RevisePrompt({
  defaultValue,
  onRefine,
}: {
  defaultValue: string;
  onRefine?: (instruction: string) => void;
}) {
  const [value, setValue] = useState(defaultValue);

  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <p className="text-label-caps uppercase text-secondary">Refine selection</p>
      <div className="mt-2 flex items-center gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="flex-1 rounded-sm border border-border bg-neutral px-3 py-2 text-body text-primary outline-none focus:border-primary"
          placeholder="How should this be revised?"
        />
        <button
          type="button"
          onClick={() => onRefine?.(value)}
          className="shrink-0 rounded-sm bg-cta px-4 py-2 text-body-sm text-on-cta transition-colors hover:bg-cta-hover"
        >
          Refine
        </button>
      </div>
    </div>
  );
}
