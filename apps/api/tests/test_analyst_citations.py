"""W0 — Analyst citations integration.

Exercises ``analyst.run_with_citations`` end-to-end against the demo Rotterdam
fixture with the picker stubbed (we do NOT call the model in tests). The
underlying BM25 corpus search runs for real so the assertion that *The Mexico
1* surfaces as a candidate for the weather event is a real signal: if the
corpus is reshuffled or rephrased, the test catches it.

The acceptance criteria from the architecture spec:

1. Running the Rotterdam case produces at least one verified citation per
   flagged event.
2. A faked, hallucinated citation is dropped (the picker cannot reference a
   case_id outside the candidate list, and the verify gate dumps anything
   that does not appear in the tool transcript).
3. The existing analyst.run path stays untouched.
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
from laytimely_api.agents import analyst  # noqa: E402
from laytimely_api.agents.analyst import (  # noqa: E402
    EnrichedDisputeAnalysis,
    FlaggedEventCitations,
    _CitationPick,
    _CitationPicks,
    _citations_for_event,
)
from laytimely_api.fixtures import demo_voyage_fixture  # noqa: E402
from laytimely_api.legal import corpus as legal_corpus  # noqa: E402
from laytimely_api.legal.models import CitedAuthority  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _demo_event_and_dispute():
    voyage = demo_voyage_fixture()
    assert voyage.dispute is not None
    flagged = voyage.dispute.flagged_events
    assert flagged, "demo fixture should have at least one flagged event"
    return voyage, flagged[0]


def _stub_pick(monkeypatch: pytest.MonkeyPatch, picks: list[_CitationPick]) -> None:
    """Patch ``analyst._pick_citations`` to return a fixed picks list.

    Tests use this to drive the picker deterministically; the BM25 corpus
    search beneath runs for real.
    """

    async def fake(event, candidates):  # type: ignore[no-untyped-def]
        return _CitationPicks(picks=picks)

    monkeypatch.setattr(analyst, "_pick_citations", fake)


# ---------------------------------------------------------------------------
# BM25 surfaces The Mexico 1 for the demo weather event
# ---------------------------------------------------------------------------


def test_demo_weather_event_query_surfaces_mexico_in_candidates() -> None:
    """Sanity check that the weather event's facts BM25-rank the right case.

    The picker call is the only LLM dependency; the candidate list is fully
    deterministic. If the corpus shifts so that *The Mexico 1* falls out of
    the top-5 for the demo event, the rest of the contract still holds but
    the demo loses its golden citation, which this test surfaces immediately.
    """
    _, event = _demo_event_and_dispute()
    query = analyst._citation_query(event)
    hits = legal_corpus.search(query, k=analyst._CITATION_TOP_K)
    assert any(h.case_id == "the-mexico-1-1990" for h in hits), (
        "demo weather event no longer ranks The Mexico 1 in the top-K"
    )


# ---------------------------------------------------------------------------
# End-to-end: picker chooses Mexico 1, returns a verified CitedAuthority
# ---------------------------------------------------------------------------


def test_citations_for_event_verifies_real_corpus_pick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    _stub_pick(
        monkeypatch,
        [
            _CitationPick(
                case_id="the-mexico-1-1990",
                proposition=(
                    "An express contractual condition must be satisfied "
                    "before time can be deducted from laytime under a "
                    "weather exception."
                ),
            )
        ],
    )

    cited = asyncio.run(_citations_for_event(event))

    assert len(cited) == 1
    only = cited[0]
    assert isinstance(only, CitedAuthority)
    assert only.citation == "The Mexico 1 [1990] 1 Lloyd's Rep 507"
    assert only.verified_via_tool is True
    assert only.tool_used == "corpus"
    assert "express contractual condition" in only.proposition


# ---------------------------------------------------------------------------
# Slop killer: a fake case_id is dropped
# ---------------------------------------------------------------------------


def test_hallucinated_case_id_is_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    _stub_pick(
        monkeypatch,
        [
            _CitationPick(
                case_id="not-a-real-case-9999",
                proposition="fabricated authority",
            )
        ],
    )

    cited = asyncio.run(_citations_for_event(event))
    assert cited == [], (
        "picker returning a case_id not in the candidate list must yield "
        "an empty citation list"
    )


def test_mix_of_real_and_hallucinated_keeps_only_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    _stub_pick(
        monkeypatch,
        [
            _CitationPick(
                case_id="not-a-real-case-9999",
                proposition="fabricated authority",
            ),
            _CitationPick(
                case_id="the-mexico-1-1990",
                proposition="real authority on weather exceptions",
            ),
        ],
    )

    cited = asyncio.run(_citations_for_event(event))
    assert [c.citation for c in cited] == [
        "The Mexico 1 [1990] 1 Lloyd's Rep 507"
    ]


# ---------------------------------------------------------------------------
# Cap + de-duplication
# ---------------------------------------------------------------------------


def test_picks_are_capped_per_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    query = analyst._citation_query(event)
    candidates = legal_corpus.search(query, k=analyst._CITATION_TOP_K)
    assert len(candidates) >= analyst._CITATIONS_PER_EVENT_CAP, (
        "need at least 3 candidates to exercise the cap"
    )

    _stub_pick(
        monkeypatch,
        [
            _CitationPick(case_id=hit.case_id, proposition="ok")
            for hit in candidates
        ],
    )
    cited = asyncio.run(_citations_for_event(event))
    assert len(cited) == analyst._CITATIONS_PER_EVENT_CAP


def test_duplicate_case_ids_are_deduped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    _stub_pick(
        monkeypatch,
        [
            _CitationPick(case_id="the-mexico-1-1990", proposition="first"),
            _CitationPick(case_id="the-mexico-1-1990", proposition="second"),
        ],
    )
    cited = asyncio.run(_citations_for_event(event))
    assert len(cited) == 1
    assert cited[0].proposition == "first"


def test_empty_proposition_is_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, event = _demo_event_and_dispute()
    _stub_pick(
        monkeypatch,
        [
            _CitationPick(case_id="the-mexico-1-1990", proposition="   "),
        ],
    )
    assert asyncio.run(_citations_for_event(event)) == []


# ---------------------------------------------------------------------------
# Top-level run_with_citations stitches per-event results together
# ---------------------------------------------------------------------------


def test_run_with_citations_attaches_per_event_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    voyage = demo_voyage_fixture()
    assert voyage.extraction is not None
    assert voyage.laytime is not None
    assert voyage.dispute is not None

    async def fake_run(extraction, laytime, perspective):  # type: ignore[no-untyped-def]
        return voyage.dispute

    _stub_pick(
        monkeypatch,
        [
            _CitationPick(
                case_id="the-mexico-1-1990",
                proposition="weather exception requires express threshold",
            )
        ],
    )
    monkeypatch.setattr(analyst, "run", fake_run)

    enriched = asyncio.run(
        analyst.run_with_citations(
            voyage.extraction, voyage.laytime, voyage.perspective
        )
    )

    assert isinstance(enriched, EnrichedDisputeAnalysis)
    assert enriched.analysis is voyage.dispute
    assert len(enriched.citations) == 1
    bundle = enriched.citations[0]
    assert isinstance(bundle, FlaggedEventCitations)
    assert bundle.event_id == "e6"
    assert [a.citation for a in bundle.cited_authorities] == [
        "The Mexico 1 [1990] 1 Lloyd's Rep 507"
    ]


def test_run_with_citations_skips_events_with_no_picks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the picker returns no picks for an event, the event is omitted
    from the citations sibling list (rather than appearing with an empty
    authorities list)."""
    voyage = demo_voyage_fixture()
    assert voyage.extraction is not None
    assert voyage.laytime is not None
    assert voyage.dispute is not None

    async def fake_run(extraction, laytime, perspective):  # type: ignore[no-untyped-def]
        return voyage.dispute

    _stub_pick(monkeypatch, [])  # empty picks list
    monkeypatch.setattr(analyst, "run", fake_run)

    enriched = asyncio.run(
        analyst.run_with_citations(
            voyage.extraction, voyage.laytime, voyage.perspective
        )
    )
    assert enriched.citations == []


# ---------------------------------------------------------------------------
# Existing analyst.run contract is unchanged
# ---------------------------------------------------------------------------


def test_run_still_returns_dispute_analysis_without_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``analyst.run`` is the legacy entrypoint; nothing about it changed.

    Asserts that we did not accidentally fold citations into the unenriched
    path. Stubs extract_structured to avoid a real Anthropic call.
    """
    voyage = demo_voyage_fixture()
    assert voyage.extraction is not None
    assert voyage.laytime is not None
    assert voyage.dispute is not None

    async def fake_extract(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return voyage.dispute

    monkeypatch.setattr(analyst, "extract_structured", fake_extract)

    result = asyncio.run(
        analyst.run(voyage.extraction, voyage.laytime, voyage.perspective)
    )
    # Returns the unwrapped DisputeAnalysis, not an EnrichedDisputeAnalysis.
    assert result.flagged_events[0].event_id == "e6"
    assert not hasattr(result, "citations")
