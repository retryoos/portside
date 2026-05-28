// The formal claim letter "sheet" (DESIGN.md §Screens 2). White surface, serif
// throughout: section label "TO: CHARTERERS", the serif hero figure (NOT mono),
// then the letter body from packet.claim_letter_markdown via react-markdown.
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
      className="rounded-md border border-border bg-surface p-8 md:p-12"
    >
      <p className="text-label-caps text-secondary">To: Charterers</p>

      <p className="mt-6 text-hero-figure text-primary">
        Demurrage due to owners: {formatEur(packet.quantum_eur)}
      </p>

      <div className="mt-8 text-letter-body text-primary">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="mt-6 text-h2 text-primary">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="mt-6 text-h3 text-primary">{children}</h2>
            ),
            p: ({ children }) => <p className="mt-4">{children}</p>,
            strong: ({ children }) => (
              <strong className="font-medium">{children}</strong>
            ),
            ul: ({ children }) => (
              <ul className="mt-3 list-disc space-y-1 pl-5">{children}</ul>
            ),
            li: ({ children }) => <li>{children}</li>,
            em: ({ children }) => <em className="italic">{children}</em>,
            a: ({ children, href }) => (
              <a href={href} className="text-primary underline">
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
