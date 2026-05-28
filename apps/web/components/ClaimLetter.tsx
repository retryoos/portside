// The formal claim letter "sheet" (DESIGN.md "Surfaces"). White card, Inter
// throughout: section label "TO: CHARTERERS", the prominent hero figure, then the
// letter body from packet.claim_letter_markdown via react-markdown.
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { demoVoyage } from "@/lib/demo";
import { formatEur } from "@/lib/format";
import type { ClaimPacket } from "@/lib/types";

export const LETTER_DOM_ID = "claim-letter-sheet";

export default function ClaimLetter({
  packet = demoVoyage.packet,
}: {
  packet?: ClaimPacket | null;
}) {
  if (!packet) return null;

  return (
    <article
      id={LETTER_DOM_ID}
      className="rounded-xl border border-border bg-surface p-8 md:p-12"
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
          {packet.claim_letter_markdown}
        </ReactMarkdown>
      </div>
    </article>
  );
}
