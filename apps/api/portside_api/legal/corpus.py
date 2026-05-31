"""BM25 search + exact-citation lookup over the curated case-law corpus.

The corpus is a JSONL committed next to this module. Loaded once at import,
indexed once with rank-bm25, queried in-process. No service, no model. The
output ``CaseHit`` carries the headnote and the citation token; the agent uses
those to build a ``CitedAuthority`` whose ``verified_via_tool`` must be True.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

from .models import CaseHit, CorpusEntry

_CORPUS_PATH = Path(__file__).resolve().parent / "corpus.jsonl"


def _tokenize(text: str) -> list[str]:
    """Lowercase token split, alphanumeric only. BM25 wants a token list."""
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=1)
def _load() -> tuple[list[CorpusEntry], BM25Okapi]:
    """Read corpus.jsonl and build a BM25 index over the searchable fields.

    Search corpus: citation + headnote + topics + court + year. The topics tag
    weight is captured by repeating each tag twice so a topic-aligned query
    biases toward topic-aligned cases.
    """
    entries: list[CorpusEntry] = []
    with _CORPUS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(CorpusEntry.model_validate_json(line))

    def doc_tokens(e: CorpusEntry) -> list[str]:
        topic_block = " ".join(e.topics) + " " + " ".join(e.topics)  # weight x2
        return _tokenize(
            f"{e.citation} {e.headnote} {topic_block} {e.court} {e.year}"
        )

    index = BM25Okapi([doc_tokens(e) for e in entries])
    return entries, index


def all_entries() -> list[CorpusEntry]:
    """Convenience: return the corpus rows. Used by tests and by `lookup_case`."""
    entries, _ = _load()
    return list(entries)


def search(
    query: str, topic_filter: Optional[str] = None, k: int = 5
) -> list[CaseHit]:
    """BM25 top-k. ``topic_filter`` restricts the candidates to cases tagged
    with that topic. Empty query returns []."""
    if not query.strip():
        return []
    entries, index = _load()
    candidates = (
        entries
        if topic_filter is None
        else [e for e in entries if topic_filter in e.topics]
    )
    if not candidates:
        return []
    if topic_filter is not None:
        # Rebuild a tiny index over the filtered subset so the BM25 statistics
        # reflect the candidate pool (small corpora make this cheap).
        sub_index = BM25Okapi(
            [
                _tokenize(
                    f"{e.citation} {e.headnote} {' '.join(e.topics)} {e.court} {e.year}"
                )
                for e in candidates
            ]
        )
        scores = sub_index.get_scores(_tokenize(query))
    else:
        scores = index.get_scores(_tokenize(query))

    ranked = sorted(zip(candidates, scores), key=lambda t: t[1], reverse=True)
    hits: list[CaseHit] = []
    for entry, score in ranked[:k]:
        if score <= 0.0:
            continue
        hits.append(
            CaseHit(
                case_id=entry.case_id,
                citation=entry.citation,
                headnote=entry.headnote,
                url=entry.url,
                score=float(score),
            )
        )
    return hits


def lookup_case(citation: str) -> Optional[CorpusEntry]:
    """Exact-string match on the citation token. Used to confirm a citation the
    model remembers rather than to discover one."""
    needle = citation.strip().lower()
    if not needle:
        return None
    for entry in all_entries():
        if entry.citation.lower() == needle:
            return entry
    return None
