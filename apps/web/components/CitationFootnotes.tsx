"use client";

// Bottom-of-letter "Authorities cited" block (W5,
// notes/architecture_weeks_5_to_8.md §1.6). Numbered list matching the
// superscript markers injected into the letter body via injectCitationMarkers.
// Renders inside the letter article so it scrolls with the body and shows up
// in PDF / Word exports without extra wiring.

import { toSuperscript, type NumberedAuthority } from "@/lib/letter-citations";

export default function CitationFootnotes({
  authorities,
}: {
  authorities: NumberedAuthority[];
}) {
  if (authorities.length === 0) return null;
  return (
    <aside
      aria-label="Authorities cited"
      className="mt-10 rounded-md border border-border bg-surface-muted px-5 py-4"
      contentEditable={false}
      suppressContentEditableWarning
    >
      <p className="text-eyebrow text-secondary">Authorities cited</p>
      <ol className="mt-3 space-y-2 text-body-sm text-primary">
        {authorities.map((a) => (
          <li
            key={`${a.citation}-${a.index}`}
            className="flex items-start gap-2"
          >
            <span
              aria-hidden
              className="tabular-nums text-secondary"
              style={{ minWidth: "1.5rem" }}
            >
              {toSuperscript(a.index)}
            </span>
            <span className="flex-1">
              <span className="font-medium">
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
              </span>
              <span className="text-secondary"> {a.proposition}</span>
            </span>
          </li>
        ))}
      </ol>
    </aside>
  );
}
