"use client";

// Client-side PDF export (notes/06-frontend.md §6 — no backend endpoint).
// Runs html2pdf.js (dynamic import) on the letter DOM node identified by
// targetId. Ghost-style button; this is NOT the one ink primary action.
import { useState } from "react";

export default function ExportPdfButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);

  async function handleExport() {
    const node = document.getElementById(targetId);
    if (!node) return;
    setBusy(true);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      await html2pdf()
        .set({
          margin: [16, 16, 16, 16],
          filename: "Aegean-Pioneer-demurrage-claim.pdf",
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, backgroundColor: "#FFFFFF", useCORS: true },
          jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
          pagebreak: { mode: ["css", "legacy"] },
        })
        .from(node)
        .save();
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={busy}
      className="rounded-full px-4 py-2.5 text-body-sm font-medium text-secondary transition-colors hover:text-primary disabled:opacity-50"
    >
      {busy ? "Exporting…" : "Export full case file (PDF)"}
    </button>
  );
}
