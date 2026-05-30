"use client";

// Upload entry for a live voyage (notes/15-next-phase.md: Agent 2 frontend
// wiring). Collects the three PDFs + perspective and hands them up to ClaimScreen,
// which calls createVoyage + pollVoyage. "Try the demo voyage" is the offline
// fallback that renders lib/demo.ts without touching the backend.
import { useState } from "react";
import type { VoyageFiles } from "@/lib/api";

type Role = "cp" | "nor" | "sof";

const ROLES: { id: Role; label: string }[] = [
  { id: "cp", label: "Charter Party" },
  { id: "nor", label: "Notice of Readiness" },
  { id: "sof", label: "Statement of Facts" },
];

export default function Dropzone({
  onSubmit,
  busy = false,
}: {
  onSubmit: (files: VoyageFiles) => void;
  busy?: boolean;
}) {
  const [files, setFiles] = useState<Partial<Record<Role, File>>>({});

  const ready = ROLES.every((r) => files[r.id]);

  function handleSubmit() {
    if (!ready) return;
    onSubmit({ cp: files.cp!, nor: files.nor!, sof: files.sof! });
  }

  return (
    <section className="rounded-xl border border-border bg-surface p-6 md:p-7">
      <p className="text-label-caps text-secondary">Run a live voyage</p>
      <p className="mt-2 text-body-sm text-secondary">
        Upload the three voyage documents (PDF) and the pipeline drafts the claim
        packet end to end.
      </p>

      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {ROLES.map((r) => {
          const picked = files[r.id];
          return (
            <label key={r.id} className="block">
              <span className="text-label-caps text-secondary">{r.label}</span>
              <div className="mt-2 flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className={`inline-flex cursor-pointer items-center rounded-full border border-border bg-surface-muted px-3.5 py-1.5 text-body-sm font-medium text-primary transition-colors hover:bg-border ${busy ? "pointer-events-none opacity-50" : ""}`}
                >
                  Choose File
                </span>
                <span className="min-w-0 flex-1 truncate text-body-sm text-secondary">
                  {picked ? picked.name : "no file selected"}
                </span>
              </div>
              <input
                type="file"
                accept="application/pdf,.pdf"
                disabled={busy}
                onChange={(e) =>
                  setFiles((prev) => ({ ...prev, [r.id]: e.target.files?.[0] }))
                }
                className="sr-only"
              />
            </label>
          );
        })}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!ready || busy}
          className="rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover disabled:opacity-50"
        >
          {busy ? "Processing…" : "Process voyage"}
        </button>
      </div>
    </section>
  );
}
