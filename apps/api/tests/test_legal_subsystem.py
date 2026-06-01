"""Tests for the legal citation subsystem (notes/architecture_weeks_5_to_8.md §1.6).

Three blocks:

- ``corpus``: BM25 ranks the right cases at the top for the demo weather
  argument; exact citation lookup returns the canonical row.
- ``imo``: convention article lookup is case- and whitespace-insensitive.
- ``verify``: unverified citations are dropped; verified ones pass; an empty
  transcript means nothing passes.

EUR-Lex live calls are blocked by default (settings flag off); we assert the
client raises LiveCallDisabled rather than hitting the network.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from laytimely_api.legal import corpus, eur_lex, imo, verify  # noqa: E402
from laytimely_api.legal.models import CitedAuthority  # noqa: E402
from laytimely_api.legal.outbound import LiveCallDisabled, OutboundClient  # noqa: E402


# ---------------------------------------------------------------------------
# Corpus search + exact lookup
# ---------------------------------------------------------------------------


def test_corpus_search_finds_mexico_for_weather_query() -> None:
    hits = corpus.search(
        "weather stoppage precipitation threshold exception",
        topic_filter="weather_exception",
    )
    assert hits, "BM25 returned no hits for the weather query"
    assert "the-mexico-1-1990" in {h.case_id for h in hits[:3]}


def test_corpus_topic_filter_excludes_off_topic_cases() -> None:
    # 'arrived_ship' is a different topic; should not surface The Mexico 1.
    hits = corpus.search("weather stoppage", topic_filter="arrived_ship")
    assert "the-mexico-1-1990" not in {h.case_id for h in hits}


def test_corpus_empty_query_returns_empty() -> None:
    assert corpus.search("") == []
    assert corpus.search("   ") == []


def test_corpus_exact_lookup_returns_full_row() -> None:
    entry = corpus.lookup_case("The Mexico 1 [1990] 1 Lloyd's Rep 507")
    assert entry is not None
    assert entry.case_id == "the-mexico-1-1990"
    assert "precipitation" in entry.headnote.lower()


def test_corpus_lookup_unknown_citation_returns_none() -> None:
    assert corpus.lookup_case("The Made Up Ship [2099] 99 Lloyd's Rep 1") is None


def test_corpus_search_ranks_relevant_topic_above_others() -> None:
    hits = corpus.search("notice of readiness arrived ship anchorage")
    case_ids = [h.case_id for h in hits]
    # The Johanna Oldendorff is the canonical NOR / arrived-ship case.
    assert "the-johanna-oldendorff-1974" in case_ids[:3]


# ---------------------------------------------------------------------------
# IMO conventions
# ---------------------------------------------------------------------------


def test_imo_lookup_returns_verbatim_article_text() -> None:
    article = imo.lookup("hague_visby", "III r 6")
    assert article is not None
    assert "one year" in article.text.lower()
    assert article.url is not None


def test_imo_lookup_is_whitespace_and_case_insensitive() -> None:
    a1 = imo.lookup("hague_visby", "iii  r 6")
    a2 = imo.lookup("hague_visby", "III r 6")
    assert a1 is not None and a2 is not None
    assert a1.text == a2.text


def test_imo_lookup_unknown_returns_none() -> None:
    assert imo.lookup("hague_visby", "X r 99") is None
    assert imo.lookup("not_a_convention", "I r 1") is None


# ---------------------------------------------------------------------------
# Verification gate
# ---------------------------------------------------------------------------


def _auth(citation: str, *, verified: bool = True) -> CitedAuthority:
    return CitedAuthority(
        citation=citation,
        verified_via_tool=verified,
        tool_used="corpus",
        proposition="test",
    )


def test_verify_drops_when_transcript_empty() -> None:
    assert verify.validate_authorities([_auth("The Mexico 1 [1990] 1 Lloyd's Rep 507")], []) == []


def test_verify_drops_when_verified_flag_false() -> None:
    transcript = ["The Mexico 1 [1990] 1 Lloyd's Rep 507"]
    assert (
        verify.validate_authorities(
            [_auth("The Mexico 1 [1990] 1 Lloyd's Rep 507", verified=False)],
            transcript,
        )
        == []
    )


def test_verify_keeps_when_citation_appears_in_transcript() -> None:
    transcript = [
        "Hit 1: The Mexico 1 [1990] 1 Lloyd's Rep 507 headnote text...",
        "Hit 2: another case",
    ]
    kept = verify.validate_authorities(
        [_auth("The Mexico 1 [1990] 1 Lloyd's Rep 507")], transcript
    )
    assert [a.citation for a in kept] == ["The Mexico 1 [1990] 1 Lloyd's Rep 507"]


def test_verify_normalises_whitespace_and_case() -> None:
    transcript = ["the mexico 1 [1990] 1 lloyd's rep 507"]
    auth = _auth("The   Mexico 1 [1990] 1 Lloyd's Rep 507")
    assert verify.validate_authorities([auth], transcript) == [auth]


def test_verify_drops_unverifiable_alongside_kept_ones() -> None:
    transcript = ["The Mexico 1 [1990] 1 Lloyd's Rep 507 — weather"]
    inputs = [
        _auth("The Mexico 1 [1990] 1 Lloyd's Rep 507"),
        _auth("The Fictional 2 [2099] 99 Lloyd's Rep 1"),
    ]
    kept = verify.validate_authorities(inputs, transcript)
    assert [a.citation for a in kept] == ["The Mexico 1 [1990] 1 Lloyd's Rep 507"]


# ---------------------------------------------------------------------------
# Outbound + EUR-Lex: blocked when off
# ---------------------------------------------------------------------------


def test_outbound_blocks_when_live_off() -> None:
    client = OutboundClient("https://example.invalid/", live=False)
    with pytest.raises(LiveCallDisabled):
        asyncio.run(client.get("/anything"))


def test_eur_lex_search_returns_empty_when_off() -> None:
    eur_lex.reset()
    hits = asyncio.run(eur_lex.search("MARPOL Annex VI", live=False))
    assert hits == []
