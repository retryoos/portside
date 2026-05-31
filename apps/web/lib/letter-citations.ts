// Pure helpers for stitching CitedAuthority markers into the letter body
// (W5, notes/architecture_weeks_5_to_8.md §1.6).
//
// Two outputs from one pass:
//   - the rewritten markdown with superscript numerals appended after every
//     citation token reference (¹ ² ³ ...).
//   - a flat ordered list of the unique authorities, numbered to match.
//
// One-pass regex alternation rather than sequential replace() calls so we
// never double-mark a citation (the second pass would otherwise see the
// already-marked token and stack another superscript on top). Longer
// citations are matched first to handle the rare case where one citation is
// a substring of another.

import type {
  CitedAuthority,
  FlaggedEventCitations,
} from "./types";

export interface NumberedAuthority extends CitedAuthority {
  index: number;
}

export interface CitationInjectionResult {
  markdown: string;
  flat: NumberedAuthority[];
}

const SUPERSCRIPT_DIGITS: Record<string, string> = {
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
};

export function toSuperscript(n: number): string {
  return String(n)
    .split("")
    .map((d) => SUPERSCRIPT_DIGITS[d] ?? d)
    .join("");
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * De-dupe the per-event bundles into a flat ordered list. Order is
 * event-iteration order (the analyst's own ordering of flagged events) then
 * the per-event citation order; first occurrence wins, later duplicates fold
 * into the same number.
 */
export function flattenCitations(
  bundles: FlaggedEventCitations[],
): NumberedAuthority[] {
  const flat: NumberedAuthority[] = [];
  const seen = new Set<string>();
  for (const bundle of bundles) {
    for (const authority of bundle.cited_authorities) {
      const key = authority.citation.trim();
      if (seen.has(key)) continue;
      seen.add(key);
      flat.push({ ...authority, index: flat.length + 1 });
    }
  }
  return flat;
}

/**
 * Append a unicode superscript marker after every reference to a numbered
 * authority in the markdown. Single-pass replace via an alternation regex so
 * repeated authorities all pick up the same marker without stacking.
 */
export function injectCitationMarkers(
  markdown: string,
  bundles: FlaggedEventCitations[],
): CitationInjectionResult {
  const flat = flattenCitations(bundles);
  if (flat.length === 0) return { markdown, flat };

  // Longest first to avoid a shorter token matching inside a longer one.
  const sorted = [...flat].sort(
    (a, b) => b.citation.length - a.citation.length,
  );
  const pattern = new RegExp(
    sorted.map((entry) => escapeRegex(entry.citation)).join("|"),
    "g",
  );
  const supByCitation = new Map(
    flat.map((entry) => [entry.citation, toSuperscript(entry.index)]),
  );

  const next = markdown.replace(pattern, (match) => {
    const sup = supByCitation.get(match);
    return sup ? `${match}${sup}` : match;
  });
  return { markdown: next, flat };
}
