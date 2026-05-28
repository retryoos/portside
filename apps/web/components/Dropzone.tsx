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
  onDemo,
  busy = false,
}: {
  onSubmit: (files: VoyageFiles) => void;
  onDemo: () => void;
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
        {ROLES.map((r) => (
          <label key={r.id} className="block">
            <span className="text-label-caps text-secondary">{r.label}</span>
            <input
              type="file"
              accept="application/pdf,.pdf"
              disabled={busy}
              onChange={(e) =>
                setFiles((prev) => ({ ...prev, [r.id]: e.target.files?.[0] }))
              }
              className="mt-2 block w-full text-body-sm text-secondary file:mr-3 file:rounded-full file:border file:border-border file:bg-surface-muted file:px-3.5 file:py-1.5 file:text-body-sm file:font-medium file:text-primary hover:file:bg-border"
            />
            {files[r.id] && (
              <span className="mt-1 block truncate text-body-sm text-secondary">
                {files[r.id]!.name}
              </span>
            )}
          </label>
        ))}
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

        <button
          type="button"
          onClick={onDemo}
          disabled={busy}
          className="rounded-full px-4 py-2.5 text-body-sm font-medium text-secondary transition-colors hover:text-primary disabled:opacity-50"
        >
          Try the demo voyage
        </button>
      </div>
    </section>
  );
}
