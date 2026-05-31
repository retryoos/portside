"use client";

// Word export button (notes/architecture_weeks_5_to_8.md §1.2). Mirrors
// ExportPdfButton: walks the same contentEditable letter DOM (#targetId) so
// any browser edits flow through to the .docx, exactly as they flow through
// to the PDF.
//
// docx + file-saver are dynamically imported on click so the marketing
// bundle does not pull in either dependency. Same trick as the PDF export.

import { useState } from "react";

export default function ExportDocxButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleExport() {
    const node = document.getElementById(targetId);
    if (!node) {
      console.error(`Word export: element #${targetId} not found`);
      setFailed(true);
      return;
    }

    setFailed(false);
    setBusy(true);
    try {
      const [{ letterToDocx }, { saveAs }] = await Promise.all([
        import("./letter-to-docx"),
        import("file-saver"),
      ]);
      const blob = await letterToDocx(node as HTMLElement);
      const filename = makeFilename(node);
      saveAs(blob, filename);
    } catch (err) {
      console.error("Word export failed", err);
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  const label = busy
    ? "Exporting…"
    : failed
      ? "Export failed, retry"
      : "Download Word";
  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={busy}
      aria-label={label}
      title={label}
      className="flex h-9 w-9 items-center justify-center rounded-full text-primary transition-colors hover:bg-surface-muted disabled:opacity-50"
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        {/* Document outline + a "W" mark inside. */}
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <path d="M9 13l1 4 2-3 2 3 1-4" />
      </svg>
    </button>
  );
}

function makeFilename(node: HTMLElement): string {
  // Try to read the vessel name from a dataset attribute the case-detail
  // page sets on the letter article; fall back to a generic name.
  const vessel = node.dataset.vessel?.trim().replace(/\s+/g, "-") ?? "voyage";
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return `demurrage-claim-${vessel}-${today}.docx`;
}
