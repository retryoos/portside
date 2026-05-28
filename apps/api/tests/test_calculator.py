"""The calculator gate (notes/09-pre-merge-protocol.md Check 2, 15-next-phase.md).

Locks the deterministic Agent 2b arithmetic against the single-source-of-truth
demo voyage (MT Aegean Pioneer, Ras Tanura -> Rotterdam): 72h allowed, 117h
used, 45h on demurrage at EUR 1,875/hr -> EUR 84,375.00.

If this fails, do not merge — the quantum is the demo's headline number.
"""

from portside_api.agents.calculator import calculate_laytime
from portside_api.fixtures import demo_voyage_fixture


def _inputs():
    state = demo_voyage_fixture()
    assert state.extraction is not None
    assert state.laytime is not None
    return state.extraction, state.laytime.classifications


def test_quantum_matches_source_of_truth():
    extraction, classifications = _inputs()
    result = calculate_laytime(extraction, classifications)
    assert result.laytime_allowed_hours == 72.0
    assert result.laytime_used_hours == 117.0
    assert result.time_on_demurrage_hours == 45.0
    assert result.time_excepted_hours == 0.0
    assert result.demurrage_rate_per_hour_eur == 1875.0
    assert result.demurrage_due_eur == 84375.0


def test_rows_and_contested():
    extraction, classifications = _inputs()
    result = calculate_laytime(extraction, classifications)
    # running total is monotonic non-decreasing
    totals = [r.running_total_hours for r in result.rows]
    assert totals == sorted(totals)
    # final running total equals used hours
    assert result.rows[-1].running_total_hours == result.laytime_used_hours
    # exactly the weather stoppage (e6->e7) is contestable
    contested = [r for r in result.rows if r.contestable]
    assert len(contested) == 1
    assert contested[0].event_id_start == "e6"


def test_matches_fixture_summary():
    """Calculator output must reconcile with the committed fixture's laytime."""
    state = demo_voyage_fixture()
    assert state.laytime is not None
    computed = calculate_laytime(state.extraction, state.laytime.classifications)  # type: ignore[arg-type]
    assert computed.demurrage_due_eur == state.laytime.demurrage_due_eur
    assert computed.laytime_used_hours == state.laytime.laytime_used_hours
