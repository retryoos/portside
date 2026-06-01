"""Unit tests for the offline-fixture export script.

Guards the wire-shape: by_alias=True is mandatory because the frontend types
(apps/web/lib/types.ts) expect LaytimeRow.from / .to, not Python's
from_ts/to_ts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


def test_export_writes_wire_shape_json(tmp_path: Path) -> None:
    from scripts.export_demo_fixture import export   # noqa: E402

    out = export(tmp_path / "fixture.json")
    assert out.exists()
    data = json.loads(out.read_text())

    assert data["voyage_id"] == "v_aegean_pioneer"
    assert data["stage"] == "done"
    assert data["laytime"]["demurrage_due_eur"] == 84375.0
    assert data["laytime"]["laytime_used_hours"] == 117.0

    row0 = data["laytime"]["rows"][0]
    assert "from" in row0, "LaytimeRow alias 'from' missing — by_alias=True regressed"
    assert "to" in row0, "LaytimeRow alias 'to' missing — by_alias=True regressed"
    assert "from_ts" not in row0
    assert "to_ts" not in row0


def test_export_is_idempotent(tmp_path: Path) -> None:
    """Same fixture in → byte-identical JSON out (no timestamps or RNG)."""
    from scripts.export_demo_fixture import export   # noqa: E402

    out1 = export(tmp_path / "first.json")
    out2 = export(tmp_path / "second.json")
    assert out1.read_text() == out2.read_text()


def test_committed_fixture_round_trips_to_voyage_state() -> None:
    """The committed apps/web/public/demo-fixture.json must deserialise back
    to the canonical VoyageState. If you change the fixture, re-run
    `uv run python scripts/export_demo_fixture.py`."""
    from laytimely_api.schemas import VoyageState

    repo_root = Path(__file__).resolve().parents[3]
    committed = repo_root / "apps" / "web" / "public" / "demo-fixture.json"
    assert committed.exists(), (
        "apps/web/public/demo-fixture.json missing — run "
        "`uv run python scripts/export_demo_fixture.py`"
    )

    state = VoyageState.model_validate_json(committed.read_text())
    assert state.voyage_id == "v_aegean_pioneer"
    assert state.stage == "done"
    assert state.laytime is not None
    assert state.laytime.demurrage_due_eur == 84375.0
