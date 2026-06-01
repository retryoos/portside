"use client";

// Client-side PDF export (notes/06-frontend.md §6: no backend endpoint).
// Runs html2pdf.js (dynamic import) on the letter DOM node identified by
// targetId. Ghost-style button; this is NOT the one ink primary action.
import { useState } from "react";

// html2canvas (bundled in html2pdf.js) cannot parse oklch() colors and throws.
// Our design tokens (app/theme.css) are oklch, so we redefine them as the sRGB
// hex equivalents on the *cloned* capture document only. The on-screen UI keeps
// its oklch colors; only the rasterized PDF sees rgb. `!important` defeats
// Tailwind v4's @theme cascade layer, which would otherwise re-resolve the
// tokens to oklch even with our :root override appended later. Hex values are
// the sRGB approximations of the new editorial palette in apps/web/DESIGN.md.
const PDF_SAFE_TOKENS = `:root{
  --color-primary:#1f1f1f !important;--color-on-primary:#fbfbfb !important;
  --color-secondary:#6d6e72 !important;--color-neutral:#fbfbfb !important;
  --color-surface:#ffffff !important;--color-surface-muted:#f3f4f5 !important;
  --color-border:#e5e5e8 !important;--color-border-strong:#cdcdd1 !important;
  --color-cta:#1f1f1f !important;--color-on-cta:#fbfbfb !important;
  --color-cta-hover:#404040 !important;
  --color-cta-inverse:#ffffff !important;--color-on-cta-inverse:#1f1f1f !important;
  --color-cta-inverse-hover:#ededee !important;
  --color-accent:#585fcc !important;--color-accent-container:#edeffb !important;
  --color-success:#258066 !important;--color-on-success:#f7fef9 !important;
  --color-success-container:#dff1e1 !important;
  --color-warning:#97640f !important;--color-on-warning:#fffbf5 !important;
  --color-warning-container:#ffecd1 !important;
  --color-contested:#97640f !important;--color-contested-container:#ffecd1 !important;
  --color-danger:#c5371f !important;--color-on-danger:#fff9f8 !important;
  --color-danger-container:#ffe2dd !important;
  --color-glass-tint:#ffffff !important;--color-glass-tint-strong:#ffffff !important;
  --color-glass-stroke:#e5e5e8 !important;
}`;

// Recursively walk every CSS rule in every same-origin stylesheet (including
// rules nested inside @layer / @media / @supports / @container blocks, which
// Tailwind v4 uses heavily) and rewrite any declaration containing `oklch(...)`
// to a safe placeholder. We can't resolve oklch -> rgb without a color library
// so we just neutralise it: `oklch(...)` becomes `#999999`. That's only a
// visual fallback for tokens not in PDF_SAFE_TOKENS.
function scrubOklchFromStylesheets(doc: Document): void {
  for (const sheet of Array.from(doc.styleSheets)) {
    let rules: CSSRuleList | null = null;
    try {
      rules = sheet.cssRules;
    } catch {
      // Cross-origin sheet, skip silently.
      continue;
    }
    if (rules) scrubRuleList(rules);
  }
}

function scrubRuleList(rules: CSSRuleList): void {
  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i];
    if (rule instanceof CSSStyleRule) {
      const cssText = rule.style.cssText;
      if (cssText.includes("oklch")) {
        rule.style.cssText = cssText.replace(
          /oklch\([^()]*(?:\([^()]*\)[^()]*)*\)/g,
          "#999999",
        );
      }
    } else if (
      // CSSGroupingRule covers @media, @supports, @container, @layer (block)
      typeof CSSGroupingRule !== "undefined" &&
      rule instanceof CSSGroupingRule
    ) {
      scrubRuleList(rule.cssRules);
    }
  }
}

// Walk the capture target and every descendant element, and for each property
// that html2canvas reads (color, background-color, border colors, outline,
// box-shadow, fill, stroke) inline the COMPUTED value. The browser normalises
// most computed colors to rgb(); for any leftover oklch we run it through the
// canvas color parser, which serialises to rgb(). After this pass nothing in
// the subtree can resolve to oklch at render time.
function inlineSafeColors(root: HTMLElement): () => void {
  const elements = [root, ...Array.from(root.querySelectorAll<HTMLElement>("*"))];
  const previousInline: { el: HTMLElement; cssText: string }[] = [];
  const canvasCtx = (() => {
    const c = document.createElement("canvas");
    return c.getContext("2d");
  })();
  const safe = (value: string): string => {
    if (!value || !value.includes("oklch")) return value;
    if (!canvasCtx) return value.replace(/oklch\([^)]*\)/g, "#999999");
    try {
      canvasCtx.fillStyle = "#000";
      canvasCtx.fillStyle = value;
      return canvasCtx.fillStyle;
    } catch {
      return "#999999";
    }
  };

  const PROPS = [
    "color",
    "background-color",
    "border-top-color",
    "border-right-color",
    "border-bottom-color",
    "border-left-color",
    "outline-color",
    "text-decoration-color",
    "fill",
    "stroke",
  ] as const;

  for (const el of elements) {
    previousInline.push({ el, cssText: el.style.cssText });
    const cs = window.getComputedStyle(el);
    for (const prop of PROPS) {
      const value = cs.getPropertyValue(prop);
      if (!value) continue;
      el.style.setProperty(prop, safe(value));
    }
  }

  return () => {
    for (const { el, cssText } of previousInline) {
      el.style.cssText = cssText;
    }
  };
}

export default function ExportPdfButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleExport() {
    const node = document.getElementById(targetId);
    if (!node) {
      console.error(`PDF export: element #${targetId} not found`);
      setFailed(true);
      return;
    }
    setFailed(false);
    setBusy(true);
    // The on-screen letter is a padded, bordered card; for the PDF the page
    // margin is the only padding we want. Strip the card chrome for the capture
    // so the one-page letter does not spill onto a blank second page.
    const prev = {
      padding: node.style.padding,
      border: node.style.border,
      borderRadius: node.style.borderRadius,
      contentEditable: node.getAttribute("contenteditable"),
    };
    node.style.padding = "0";
    node.style.border = "none";
    node.style.borderRadius = "0";
    // contentEditable breaks html2canvas' cloned-document snapshot in some
    // browsers (the caret/selection state pulls in form-control rendering).
    // Drop the attribute for the capture and restore it after.
    if (prev.contentEditable !== null) {
      node.removeAttribute("contenteditable");
      // Ensure the article is not focused, a stale selection in the editable
      // article can also confuse the snapshot.
      if (document.activeElement === node) {
        (node as HTMLElement).blur();
      }
    }
    // Inline every color property on the captured subtree as rgb (via the
    // browser's own canvas parser). After this pass html2canvas can never see
    // an oklch value when it reads computed styles, regardless of what
    // Tailwind generated in cascaded rules.
    const restoreInlineColors = inlineSafeColors(node as HTMLElement);
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
            // Swap oklch tokens for hex on the clone so html2canvas can parse
            // them. Also scrub any leftover `oklch(...)` literal calls from
            // stylesheet rules (Tailwind v4 alpha modifiers like `bg-x/40`
            // compile to `oklch(from var(--x) l c h / 0.4)` which html2canvas
            // cannot parse even when the variable resolves to hex).
            onclone: (doc: Document) => {
              const style = doc.createElement("style");
              style.textContent = PDF_SAFE_TOKENS;
              doc.head.appendChild(style);
              scrubOklchFromStylesheets(doc);
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
      restoreInlineColors();
      node.style.padding = prev.padding;
      node.style.border = prev.border;
      node.style.borderRadius = prev.borderRadius;
      if (prev.contentEditable !== null) {
        node.setAttribute("contenteditable", prev.contentEditable);
      }
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
