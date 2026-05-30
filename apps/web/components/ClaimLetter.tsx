// The formal claim letter "sheet" (DESIGN.md "Surfaces"). White card, Inter
// throughout: section label "TO: CHARTERERS", the prominent hero figure, then the
// letter body from packet.claim_letter_markdown via react-markdown.
//
// While the pipeline is still drafting, `loading` is true and we render a
// shape-matched skeleton in the same outer shell so nothing shifts when the
// real content crossfades in via <Reveal>.
//
// Once drafted, the article is `contentEditable`: the user can click anywhere
// to type, edit, or delete. The markdown is snapshotted to local state on first
// render so any post-mount re-render cannot stomp on the user's edits. The PDF
// export reads the live DOM, so edits flow straight into the downloaded file.
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ExportPdfButton from "@/components/ExportPdfButton";
import Reveal from "@/components/Reveal";
import { demoVoyage } from "@/lib/demo";
import { formatEur } from "@/lib/format";
import type { ClaimPacket } from "@/lib/types";

export const LETTER_DOM_ID = "claim-letter-sheet";

export default function ClaimLetter({
  packet = demoVoyage.packet,
  loading = false,
}: {
  packet?: ClaimPacket | null;
  loading?: boolean;
}) {
  // Snapshot the markdown on first render so React's diff cannot wipe user
  // edits if the parent re-renders with the same (or newly-arrived) packet.
  // Initialised lazily so the snapshot is taken at mount time and never reset.
  const [snapshotMd, setSnapshotMd] = useState<string | null>(
    packet?.claim_letter_markdown ?? null,
  );
  useEffect(() => {
    if (snapshotMd === null && packet?.claim_letter_markdown) {
      setSnapshotMd(packet.claim_letter_markdown);
    }
  }, [packet, snapshotMd]);

  if (loading || !packet) {
    return <ClaimLetterSkeleton />;
  }

  const bodyMd = snapshotMd ?? packet.claim_letter_markdown;

  return (
    <div className="relative rounded-xl border border-border bg-surface p-5">
      {/* Download PDF: top-right of the document, outside the LETTER_DOM_ID
          so html2pdf doesn't include it in the captured page. */}
      <div className="absolute right-7 top-7 z-10">
        <ExportPdfButton targetId={LETTER_DOM_ID} />
      </div>
      <Reveal ready>
        {/* contentEditable on the whole article: the user can click anywhere
            and type / edit / delete. suppressContentEditableWarning silences
            React's warning about managed children — safe here because
            `bodyMd` is the one-time snapshot above, so React will not
            reconcile inner DOM after mount. */}
        <article
          id={LETTER_DOM_ID}
          contentEditable
          suppressContentEditableWarning
          spellCheck
          aria-label="Editable claim letter"
          // Note: no focus ring via Tailwind alpha modifiers (e.g. ring-accent/40)
          // — those compile to oklch(from ...) which html2canvas can't parse and
          // would break PDF export. The blinking caret + browser default focus
          // outline are sufficient indication that the article is editable.
          className="rounded-lg bg-surface-muted p-7 md:p-10 cursor-text"
        >
          <p className="text-label-caps text-secondary">To: Charterers</p>

          <div className="mt-6">
            <p className="text-body-sm text-secondary">Demurrage due to owners</p>
            <p className="mt-1 text-hero-figure text-primary tabular-nums">
              {formatEur(packet.quantum_eur)}
            </p>
          </div>

          <hr className="mt-8 border-t border-border" />

          <div className="mt-8 text-letter-body text-primary">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="mt-7 text-h2 text-primary">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="mt-7 text-h3 text-primary">{children}</h2>
                ),
                p: ({ children }) => <p className="mt-4">{children}</p>,
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                ul: ({ children }) => (
                  <ul className="mt-3 list-disc space-y-1 pl-5 marker:text-secondary">
                    {children}
                  </ul>
                ),
                li: ({ children }) => <li>{children}</li>,
                em: ({ children }) => <em className="italic">{children}</em>,
                a: ({ children, href }) => (
                  <a href={href} className="text-accent underline underline-offset-2">
                    {children}
                  </a>
                ),
              }}
            >
              {bodyMd}
            </ReactMarkdown>
          </div>
        </article>
      </Reveal>
    </div>
  );
}

// While the letter is being drafted we keep the outer glass card (the frosted
// `bg-surface` panel that sits over the LiquidBackground), but drop the inner
// letter "sheet" (the `bg-surface-muted` article) — only the animated bars
// show inside the glass. When the draft lands, the real component swaps in
// and the sheet appears together with the text under the same outer card.
// Padding matches the real component so nothing shifts at the swap.
function ClaimLetterSkeleton() {
  const BAR_WIDTHS = [
    "w-full",
    "w-[95%]",
    "w-[88%]",
    "w-full",
    "w-[92%]",
    "w-[80%]",
    "w-full",
    "w-[60%]",
  ];
  return (
    <div className="relative rounded-xl border border-border bg-surface p-5">
      <div className="p-7 md:p-10">
        <div className="h-3 w-24 rounded animate-shimmer" />

        <div className="mt-6">
          <div className="h-3 w-40 rounded animate-shimmer" />
          <div className="mt-2 h-10 w-64 rounded animate-shimmer" />
        </div>

        <div className="mt-8 space-y-3">
          {BAR_WIDTHS.slice(0, 4).map((w, i) => (
            <div key={`a${i}`} className={`h-3 ${w} rounded animate-shimmer`} />
          ))}
          <div className="mt-7 h-5 w-48 rounded animate-shimmer" />
          {BAR_WIDTHS.slice(4).map((w, i) => (
            <div key={`b${i}`} className={`h-3 ${w} rounded animate-shimmer`} />
          ))}
        </div>
      </div>
    </div>
  );
}
