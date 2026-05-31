"""Public-domain IMO convention lookup.

Loads ``imo_conventions.json`` once and serves ``ConventionArticle`` records
by (convention slug, article token). No network. The JSON ships verbatim
public-domain text so a citation is verifiable by reading the file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .models import ConventionArticle

_IMO_PATH = Path(__file__).resolve().parent / "imo_conventions.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    with _IMO_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def convention_names() -> list[str]:
    """Slugs available in the bundled corpus."""
    return list(_load().keys())


def lookup(name: str, article: str) -> Optional[ConventionArticle]:
    """Return one article by (convention name slug, article token).

    Example: ``lookup("hague_visby", "III r 6")``. Case- and whitespace-
    insensitive on the article token.
    """
    payload = _load().get(name)
    if payload is None:
        return None
    articles: dict[str, str] = payload.get("articles", {})

    def _norm(s: str) -> str:
        """Lowercase + collapsed internal whitespace, so 'III  r 6' matches
        'III r 6'."""
        return " ".join(s.lower().split())

    normalised = _norm(article)
    for raw_key, text in articles.items():
        if _norm(raw_key) == normalised:
            return ConventionArticle(
                name=name,
                article=raw_key,
                text=text,
                url=payload.get("source_url"),
            )
    return None
