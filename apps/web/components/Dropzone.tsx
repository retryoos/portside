"use client";

// Upload entry for a live voyage (notes/15-next-phase.md — Agent 2 frontend
// wiring). Collects the three PDFs + perspective and hands them up to ClaimScreen,
// which calls createVoyage + pollVoyage. "Try the demo voyage" is the offline
// fallback that renders lib/demo.ts without touching the backend.
import { useState } from "react";
import type { VoyageFiles } from "@/lib/api";
import type { Perspective } from "@/lib/types";

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
  onSubmit: (files: VoyageFiles, perspective: Perspective) => void;
  onDemo: () => void;
  busy?: boolean;
}) {
  const [files, setFiles] = useState<Partial<Record<Role, File>>>({});
  const [perspective, setPerspective] = useState<Perspective>("owner");

  const ready = ROLES.every((r) => files[r.id]);

  function handleSubmit() {
    if (!ready) return;
    onSubmit(
      { cp: files.cp!, nor: files.nor!, sof: files.sof! },
      perspective,
    );
  }

  return (
    <section className="rounded-md border border-border bg-surface p-6">
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
              className="mt-2 block w-full text-body-sm text-primary file:mr-3 file:rounded-sm file:border file:border-border file:bg-surface-muted file:px-3 file:py-1.5 file:text-body-sm file:text-primary"
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
        <fieldset className="flex items-center gap-3">
          <legend className="sr-only">Perspective</legend>
          {(["owner", "charterer"] as Perspective[]).map((p) => (
            <label key={p} className="flex items-center gap-1.5 text-body-sm text-primary">
              <input
                type="radio"
                name="perspective"
                value={p}
                checked={perspective === p}
                disabled={busy}
                onChange={() => setPerspective(p)}
              />
              <span className="capitalize">{p}</span>
            </label>
          ))}
        </fieldset>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!ready || busy}
          className="rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover disabled:opacity-50"
        >
          {busy ? "Processing…" : "Process voyage"}
        </button>

        <button
          type="button"
          onClick={onDemo}
          disabled={busy}
          className="rounded-sm px-3.5 py-2.5 text-body-sm text-secondary transition-colors hover:text-primary disabled:opacity-50"
        >
          Try the demo voyage
        </button>
      </div>
    </section>
  );
}
