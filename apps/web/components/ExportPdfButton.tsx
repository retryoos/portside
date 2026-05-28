"use client";

// Client-side PDF export (notes/06-frontend.md §6: no backend endpoint).
// Runs html2pdf.js (dynamic import) on the letter DOM node identified by
// targetId. Ghost-style button; this is NOT the one ink primary action.
import { useState } from "react";

// html2canvas (bundled in html2pdf.js) cannot parse oklch() colors and throws.
// Our design tokens (app/theme.css) are oklch, so we redefine them as the sRGB
// hex equivalents on the *cloned* capture document only. The on-screen UI keeps
// its oklch colors; only the rasterized PDF sees rgb. Gradients are flattened to
// a solid since they also carry oklch and never sit under the letter text.
const PDF_SAFE_TOKENS = `:root{
  --color-primary:#1b1d20;--color-on-primary:#f9fafb;--color-secondary:#717378;
  --color-neutral:#f8f9fa;--color-surface:#fefeff;--color-surface-muted:#f3f4f6;
  --color-border:#e4e5e8;--color-cta:#1b1d20;--color-on-cta:#f9fafb;
  --color-cta-hover:#313336;--color-accent:#4767d3;--color-accent-container:#e6eeff;
  --color-success:#318454;--color-on-success:#f7fef9;--color-success-container:#e0f5e6;
  --color-warning:#a36d24;--color-on-warning:#fffbf5;--color-warning-container:#ffebce;
  --color-contested:#a36d24;--color-contested-container:#ffebce;
  --color-danger:#c13c3b;--color-on-danger:#fff9f8;--color-danger-container:#ffe3df;
  --gradient-warm:#e4e5e8;--gradient-cool:#e4e5e8;
}`;

export default function ExportPdfButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleExport() {
    const node = document.getElementById(targetId);
    if (!node) return;
    setFailed(false);
    setBusy(true);
    // The on-screen letter is a padded, bordered card; for the PDF the page
    // margin is the only padding we want. Strip the card chrome for the capture
    // so the one-page letter does not spill onto a blank second page.
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
          html2canvas: {
            scale: 2,
            backgroundColor: "#ffffff",
            useCORS: true,
            // Swap oklch tokens for hex on the clone so html2canvas can parse them.
            onclone: (doc: Document) => {
              const style = doc.createElement("style");
              style.textContent = PDF_SAFE_TOKENS;
              doc.head.appendChild(style);
            },
          },
          jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
          // No "legacy" mode: it inserts spurious page breaks that produce the
          // trailing blank page. "avoid-all" keeps blocks intact without it.
          pagebreak: { mode: ["avoid-all", "css"] },
        })
        .from(node)
        .save();
    } catch (e) {
      console.error("PDF export failed", e);
      setFailed(true);
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
      className="rounded-full px-4 py-2.5 text-body-sm font-medium text-secondary transition-colors hover:text-primary disabled:opacity-50"
    >
      {busy
        ? "Exporting…"
        : failed
          ? "Export failed, retry"
          : "Export full case file (PDF)"}
    </button>
  );
}
