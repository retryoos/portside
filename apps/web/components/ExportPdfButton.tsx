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
    // The on-screen letter is a padded, bordered card; for the PDF the page
    // margin is the only padding we want. Capturing the card's padding + border
    // on top of the page margin pushed the content a hair past one A4 page,
    // spilling a blank second page. Strip them for the capture, then restore.
    const prev = {
      padding: node.style.padding,
      border: node.style.border,
      borderRadius: node.style.borderRadius,
    };
    node.style.padding = "0";
    node.style.border = "none";
    node.style.borderRadius = "0";
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      await html2pdf()
        .set({
          margin: [28, 32, 28, 32],
          filename: "demurrage-claim.pdf",
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, backgroundColor: "#FFFFFF", useCORS: true },
          jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
          // No "legacy" mode: it inserts spurious page breaks that produce the
          // trailing blank page. "avoid-all" keeps blocks intact without it.
          pagebreak: { mode: ["avoid-all", "css"] },
        })
        .from(node)
        .save();
    } finally {
      node.style.padding = prev.padding;
      node.style.border = prev.border;
      node.style.borderRadius = prev.borderRadius;
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={busy}
      className="rounded-sm px-3.5 py-2.5 text-body-sm text-secondary transition-colors hover:text-primary disabled:opacity-50"
    >
      {busy ? "Exporting…" : "Export full case file (PDF)"}
    </button>
  );
}
