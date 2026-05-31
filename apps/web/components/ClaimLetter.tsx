// The formal claim letter sheet. White card, Inter throughout. The hero
// quantum lives on the page above (ClaimScreen); this card carries the
// "TO: CHARTERERS" eyebrow and the letter body via react-markdown.
//
// While the pipeline is still drafting, `loading` is true and we render a
// shape-matched skeleton in the same outer card so nothing shifts when the
// real content crossfades in via <Reveal>.
//
// Once drafted, the article is `contentEditable`: the user can click anywhere
// to type, edit, or delete. The markdown is snapshotted to local state on
// first render so any post-mount re-render cannot stomp on the user's edits.
// The PDF export reads the live DOM, so edits flow straight into the
// downloaded file.
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ExportDocxButton from "@/components/ExportDocxButton";
import ExportPdfButton from "@/components/ExportPdfButton";
import ExportXlsxButton from "@/components/ExportXlsxButton";
import MailtoLetterButton from "@/components/MailtoLetterButton";
import Reveal from "@/components/Reveal";
import { demoVoyage } from "@/lib/demo";
import type { ClaimPacket } from "@/lib/types";

export const LETTER_DOM_ID = "claim-letter-sheet";

export default function ClaimLetter({
  packet = demoVoyage.packet,
  loading = false,
  voyageId = demoVoyage.voyage_id,
  vesselName,
}: {
  packet?: ClaimPacket | null;
  loading?: boolean;
  voyageId?: string;
  vesselName?: string | null;
}) {
  // Snapshot the markdown on first render so React's diff cannot wipe user
  // edits if the parent re-renders with the same (or newly arrived) packet.
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
    <div className="relative rounded-card border border-border bg-surface">
      <div className="absolute right-6 top-6 z-10 flex items-center gap-1">
        <MailtoLetterButton
          letterMarkdown={bodyMd}
          voyageId={voyageId}
          vesselName={vesselName}
        />
        <ExportXlsxButton voyageId={voyageId} vesselName={vesselName} />
        <ExportDocxButton targetId={LETTER_DOM_ID} />
        <ExportPdfButton targetId={LETTER_DOM_ID} />
      </div>
      <Reveal ready>
        <article
          id={LETTER_DOM_ID}
          contentEditable
          suppressContentEditableWarning
          spellCheck
          aria-label="Editable claim letter"
          // No focus ring via Tailwind alpha modifiers: those compile to
          // oklch(from ...) which html2canvas can't parse and would break the
          // PDF export. The blinking caret + global focus-visible ring are
          // sufficient indication that the article is editable.
          className="cursor-text px-8 py-10 md:px-12 md:py-14"
        >
          <p className="text-eyebrow text-secondary">To: Charterers</p>

          <div className="mt-10 text-letter-body text-primary">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="mt-8 text-h2 text-primary">{children}</h1>
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
                  <a href={href} className="text-primary underline underline-offset-2">
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
    <div className="relative rounded-card border border-border bg-surface">
      <div className="px-8 py-10 md:px-12 md:py-14">
        <div className="h-3 w-24 rounded animate-shimmer" />

        <div className="mt-10 space-y-3">
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
