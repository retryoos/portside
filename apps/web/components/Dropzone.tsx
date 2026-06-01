"use client";

// Upload entry for a live voyage. Collects the three PDFs (drag-and-drop or
// click to choose) and hands them up to the dashboard, which calls
// createVoyage + pollVoyage. The demo voyage is reached via the seeded
// fixture, not from here.
import { useState } from "react";
import type { VoyageFiles } from "@/lib/api";

type Role = "cp" | "nor" | "sof";

const ROLES: { id: Role; label: string }[] = [
  { id: "cp", label: "Charter Party" },
  { id: "nor", label: "Notice of Readiness" },
  { id: "sof", label: "Statement of Facts" },
];

function isPdf(file: File): boolean {
  return (
    file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
  );
}

export default function Dropzone({
  onSubmit,
  busy = false,
}: {
  onSubmit: (files: VoyageFiles) => void;
  busy?: boolean;
}) {
  const [files, setFiles] = useState<Partial<Record<Role, File>>>({});
  // Which slot is currently under a drag, for the highlight ring.
  const [dragRole, setDragRole] = useState<Role | null>(null);
  // The slot that just rejected a non-PDF drop, for a one-shot hint.
  const [rejected, setRejected] = useState<Role | null>(null);

  const ready = ROLES.every((r) => files[r.id]);

  function setFile(role: Role, file: File | undefined) {
    if (!file) return;
    if (!isPdf(file)) {
      setRejected(role);
      return;
    }
    setRejected(null);
    setFiles((prev) => ({ ...prev, [role]: file }));
  }

  function handleSubmit() {
    if (!ready) return;
    onSubmit({ cp: files.cp!, nor: files.nor!, sof: files.sof! });
  }

  return (
    <section className="rounded-card border border-border bg-surface p-7 md:p-8">
      <p className="text-eyebrow text-secondary">Run a live voyage</p>
      <p className="mt-3 max-w-2xl text-body text-secondary">
        Drag the three voyage documents (PDF) onto the slots below, or click to
        choose them. The pipeline drafts the claim packet end to end.
      </p>

      <div className="mt-7 grid gap-5 sm:grid-cols-3">
        {ROLES.map((r) => {
          const picked = files[r.id];
          const isDragging = dragRole === r.id;
          const didReject = rejected === r.id;
          return (
            <label
              key={r.id}
              onDragEnter={(e) => {
                if (busy) return;
                e.preventDefault();
                setDragRole(r.id);
              }}
              onDragOver={(e) => {
                if (busy) return;
                e.preventDefault();
                if (dragRole !== r.id) setDragRole(r.id);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setDragRole((cur) => (cur === r.id ? null : cur));
              }}
              onDrop={(e) => {
                e.preventDefault();
                setDragRole(null);
                if (busy) return;
                setFile(r.id, e.dataTransfer.files?.[0]);
              }}
              className={`block rounded-card border bg-surface-muted px-5 py-5 transition-colors ${
                isDragging
                  ? "border-primary ring-2 ring-primary/30"
                  : didReject
                    ? "border-danger"
                    : picked
                      ? "border-border-strong"
                      : "border-border hover:border-border-strong"
              } ${busy ? "pointer-events-none opacity-50" : "cursor-pointer"}`}
            >
              <span className="text-label-caps text-secondary">{r.label}</span>
              <div className="mt-3 flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="inline-flex shrink-0 items-center rounded-pill border border-border-strong bg-surface px-3.5 py-1.5 text-body-sm font-semibold text-primary"
                >
                  Choose file
                </span>
                <span className="min-w-0 flex-1 truncate text-body-sm text-secondary">
                  {picked
                    ? picked.name
                    : isDragging
                      ? "Drop the PDF"
                      : didReject
                        ? "PDF only, try again"
                        : "drag a PDF here or choose"}
                </span>
              </div>
              <input
                type="file"
                accept="application/pdf,.pdf"
                disabled={busy}
                onChange={(e) => setFile(r.id, e.target.files?.[0])}
                className="sr-only"
              />
            </label>
          );
        })}
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!ready || busy}
          className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "Processing…" : "Process voyage"}
        </button>
        {!ready && !busy && (
          <span className="text-body-sm text-secondary">
            Select all three documents to continue.
          </span>
        )}
      </div>
    </section>
  );
}
