"use client";

// Cases sub-section of the Sources tab (W5,
// notes/architecture_weeks_5_to_8.md §1.6). Lists every unique CitedAuthority
// across the voyage, with the citation token, the analyst's one-line
// proposition, the tool channel that verified it ("corpus", "imo",
// "eur_lex", "bailii"), and a link out to the source when present.
//
// The wire data already carries verified_via_tool=true for everything that
// reaches here; the backend verify gate drops anything else. The component
// is named AuthoritiesList rather than CasesTable to avoid colliding with
// the dashboard cases list of the same name.

import {
  flattenCitations,
  type NumberedAuthority,
} from "@/lib/letter-citations";
import type {
  CitedAuthorityTool,
  FlaggedEventCitations,
} from "@/lib/types";

const TOOL_LABEL: Record<CitedAuthorityTool, string> = {
  corpus: "Corpus",
  lookup: "Corpus",
  imo: "IMO",
  eur_lex: "EUR-Lex",
  bailii: "BAILII",
};

export default function AuthoritiesList({
  bundles,
}: {
  bundles: FlaggedEventCitations[];
}) {
  const flat: NumberedAuthority[] = flattenCitations(bundles);

  if (flat.length === 0) {
    return (
      <p className="rounded-card border border-border bg-surface-muted px-4 py-6 text-center text-body-sm text-secondary">
        No authorities cited yet. Citations populate once the analyst has run
        the per-event picker pass.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {flat.map((a) => (
        <li
          key={`${a.citation}-${a.index}`}
          className="rounded-lg bg-surface-muted p-4"
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-letter-body text-primary">
              {a.url ? (
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline underline-offset-2 transition-colors hover:text-secondary"
                >
                  {a.citation}
                </a>
              ) : (
                a.citation
              )}
            </p>
            <span className="shrink-0 rounded-pill border border-border bg-surface px-2 py-0.5 text-label-caps text-secondary">
              {TOOL_LABEL[a.tool_used] ?? a.tool_used}
            </span>
          </div>
          <p className="mt-2 text-body-sm text-secondary">{a.proposition}</p>
        </li>
      ))}
    </ul>
  );
}
