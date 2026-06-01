"use client";

// Client-side PDF export. Renders the live (editable) claim letter DOM to a PDF
// as real text via jsPDF (see letter-to-pdf.ts). This replaces the previous
// html2pdf.js/html2canvas approach, which rasterized the DOM and could not
// parse Tailwind v4's oklch() colours, so the export silently failed in
// production. The text render is colour-agnostic, smaller, selectable, and
// still captures in-browser edits because it reads the live DOM.
import { useEffect, useState } from "react";

export default function ExportPdfButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  // Surface a failure visibly for a few seconds (the trigger is an icon-only
  // button, so a silent catch looked like "nothing happened").
  useEffect(() => {
    if (!failed) return;
    const t = setTimeout(() => setFailed(false), 4000);
    return () => clearTimeout(t);
  }, [failed]);

  async function handleExport() {
    const node = document.getElementById(targetId);
    if (!node) {
      setFailed(true);
      return;
    }
    setFailed(false);
    setBusy(true);
    try {
      const { letterToPdf } = await import("@/components/letter-to-pdf");
      const doc = letterToPdf(node as HTMLElement);
      doc.save("demurrage-claim.pdf");
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("PDF export failed", e);
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  const label = busy
    ? "Exporting…"
    : failed
      ? "Export failed, retry"
      : "Download PDF";
  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={busy}
      aria-label={label}
      title={label}
      className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors disabled:opacity-50 ${
        failed
          ? "text-danger hover:bg-danger-container"
          : "text-primary hover:bg-surface-muted"
      }`}
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
        {/* Document outline with folded corner */}
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        {/* Download arrow inside the page */}
        <line x1="12" y1="12" x2="12" y2="18" />
        <polyline points="9 15 12 18 15 15" />
      </svg>
    </button>
  );
}
