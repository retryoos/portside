"""The slop killer (notes/architecture_weeks_5_to_8.md §1.6).

After an agent emits a list of ``CitedAuthority``, the route layer calls
``validate_authorities`` against the tool transcript that produced this run.
Any authority whose citation does not appear in any tool result is silently
dropped, the rest pass through. A log line records every drop so the
analyst's prompt regressions surface in observability instead of in customer
output.

The model is told this rule in its system prompt; if it cheats the schema
layer effectively rejects the citation by removing it. The contract:
``verified_via_tool=True`` is necessary but not sufficient. The post-call
gate is the actual verification.
"""

from __future__ import annotations

import logging
from typing import Iterable

from .models import CitedAuthority

logger = logging.getLogger("laytimely_api.legal.verify")


def validate_authorities(
    authorities: Iterable[CitedAuthority],
    transcript_texts: Iterable[str],
) -> list[CitedAuthority]:
    """Drop unverified citations.

    ``transcript_texts`` is the corpus of every text that came back from a
    tool during this run (case headnotes, IMO article texts, EUR-Lex titles).
    A citation passes if its ``citation`` string appears as a substring in
    any transcript text and the model claimed verification. The citation
    string is normalised (lowercase, collapsed whitespace) on both sides.
    """
    haystack = " || ".join(_norm(t) for t in transcript_texts if t)
    if not haystack:
        # No tool ever ran: every claimed authority is unverifiable.
        for a in authorities:
            if a.verified_via_tool:
                logger.warning(
                    "drop citation: no tool transcript available (citation=%r)",
                    a.citation,
                )
        return []

    kept: list[CitedAuthority] = []
    for a in authorities:
        norm = _norm(a.citation)
        if not a.verified_via_tool:
            logger.info("drop citation: verified_via_tool=False (citation=%r)", a.citation)
            continue
        if norm not in haystack:
            logger.warning(
                "drop citation: not in tool transcript (citation=%r tool=%s)",
                a.citation,
                a.tool_used,
            )
            continue
        kept.append(a)
    return kept


def _norm(text: str) -> str:
    """Lowercase, collapsed whitespace, square-brackets normalised. Matches
    the way humans write a citation regardless of typographic variants."""
    return " ".join(text.lower().replace("[", " [ ").replace("]", " ] ").split())
