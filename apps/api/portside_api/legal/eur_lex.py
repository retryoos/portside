"""EUR-Lex CELLAR REST client (notes/architecture_weeks_5_to_8.md §1.6).

Thin wrapper over the EU's open legal data API. Used for EU directives,
regulations, and CJEU case-law citations the compliance product (Pick 1 in
the product roadmap) will need. Stays off in tests via
``settings.legal_eur_lex_live=False``; when off, ``search`` returns an empty
list rather than touching the network.

Endpoint reference:
    https://op.europa.eu/en/web/cellar

The CELLAR endpoint accepts simple keyword queries and returns a small JSON
result set with title, CELEX number, type, and a canonical URL. We surface
only the minimal fields the citation agent needs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from .outbound import LiveCallDisabled, OutboundClient

logger = logging.getLogger("portside_api.legal.eur_lex")

# Public endpoint. CELLAR exposes a SPARQL gateway too; the REST search is
# sufficient for citation-by-title and follows simpler request shapes.
_EUR_LEX_BASE = "https://eur-lex.europa.eu/"

# Lazy module-level client. Created on first call; ``reset`` is for tests.
_client: Optional[OutboundClient] = None


def _make_client(live: bool) -> OutboundClient:
    return OutboundClient(_EUR_LEX_BASE, live=live, min_interval_s=0.2)


def reset() -> None:
    """Drop the cached client. Tests call this between cases that flip ``live``."""
    global _client
    _client = None


@dataclass(frozen=True)
class EurLexHit:
    """One row returned by ``search``. Citation format matches CELEX."""

    celex: str
    title: str
    url: str
    doc_type: str


async def search(
    query: str,
    doc_type: Optional[str] = None,
    *,
    live: bool,
    limit: int = 5,
) -> list[EurLexHit]:
    """Return up to ``limit`` hits for ``query``.

    ``live`` is passed through from settings. When False, returns []
    immediately (the agent treats EUR-Lex as unavailable, falls back to the
    corpus). Network errors return [] with a logged warning; we never raise
    out of the legal subsystem.
    """
    global _client
    if not live or not query.strip():
        return []
    if _client is None:
        _client = _make_client(live=True)
    try:
        # CELLAR's keyword search lives at /search-result with `qid` form
        # params; we use the public legal-content quick-search endpoint, which
        # accepts plain text. Real production wiring uses the SPARQL gateway;
        # this REST shape is enough for the citation use case.
        status, body = await _client.get(
            "/search-result",
            scope="EURLEX",
            text=query,
            lang="en",
            format="json",
        )
    except LiveCallDisabled:
        return []
    except Exception as exc:  # noqa: BLE001 — boundary handler for outbound
        logger.warning("EUR-Lex search failed for %r: %s", query, exc)
        return []

    if status >= 400:
        logger.warning("EUR-Lex search %r returned HTTP %d", query, status)
        return []

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("EUR-Lex search %r returned non-JSON body", query)
        return []

    hits: list[EurLexHit] = []
    # The response shape is `{ "results": [ {celex, title, type, ...}, ... ] }`.
    # We accept missing keys silently because the CELLAR schema drifts and we
    # only need the citation primitives.
    for row in payload.get("results", [])[:limit]:
        celex = (row.get("celex") or "").strip()
        if not celex:
            continue
        if doc_type and (row.get("type") or "").lower() != doc_type.lower():
            continue
        hits.append(
            EurLexHit(
                celex=celex,
                title=(row.get("title") or "").strip(),
                url=f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}",
                doc_type=(row.get("type") or "").strip(),
            )
        )
    return hits
