"""Route-level tests for ``GET /voyages/{id}/evidence-checklist`` (W3).

The deterministic builder ``evidence_checklist.build_checklist`` already has
unit-level coverage in ``test_evidence_and_strength.py``. These tests pin
the wire surface so the W3 frontend can rely on it:

- 404 on unknown voyage
- 409 when the dispute analysis hasn't landed yet
- 200 with an ``EvidenceChecklist``-shaped body for a seeded Rotterdam voyage
- ``attached`` is sensitive to ``store.record_documents`` (cp uploaded -> cp
  rows attached)
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api import main as main_mod  # noqa: E402
from portside_api.fixtures import demo_voyage_fixture  # noqa: E402
from portside_api.objects import LocalObjectStore, StoredDocument  # noqa: E402
from portside_api.schemas import VoyageState  # noqa: E402
from portside_api.storage import InMemoryStore  # noqa: E402


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))
        with TestClient(main_mod.app) as c:
            yield c


def _seed_demo(voyage_id: str = "v_aegean_pioneer") -> VoyageState:
    state = demo_voyage_fixture(voyage_id, "owner")

    async def _save() -> None:
        await main_mod.store.save(state)

    asyncio.run(_save())
    return state


def _record_docs(voyage_id: str, roles: list[str]) -> None:
    async def _record() -> None:
        await main_mod.store.record_documents(
            voyage_id,
            [
                StoredDocument(
                    role=role,
                    object_key=f"voyages/{voyage_id}/{role}.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                )
                for role in roles
            ],
        )

    asyncio.run(_record())


def test_evidence_checklist_404_when_unknown(client: TestClient) -> None:
    resp = client.get("/voyages/v_missing/evidence-checklist")
    assert resp.status_code == 404


def test_evidence_checklist_409_when_no_dispute_yet(client: TestClient) -> None:
    async def _seed() -> None:
        await main_mod.store.save(
            VoyageState(voyage_id="v_partial", perspective="owner", stage="uploaded")
        )

    asyncio.run(_seed())
    resp = client.get("/voyages/v_partial/evidence-checklist")
    assert resp.status_code == 409


def test_evidence_checklist_returns_rows_for_demo_voyage(
    client: TestClient,
) -> None:
    _seed_demo()
    _record_docs("v_aegean_pioneer", ["cp", "nor", "sof"])

    resp = client.get("/voyages/v_aegean_pioneer/evidence-checklist")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    items = body["items"]
    assert items, "demo voyage should produce at least one row"
    # Every row must carry a closed-vocabulary role; the UI relies on this.
    roles = {row["role"] for row in items}
    assert "cp_excerpt" in roles
    # CP uploaded -> every cp_excerpt row is attached.
    cp_rows = [r for r in items if r["role"] == "cp_excerpt"]
    assert all(r["attached"] for r in cp_rows)


def test_evidence_checklist_cp_unattached_when_cp_doc_missing(
    client: TestClient,
) -> None:
    _seed_demo()
    _record_docs("v_aegean_pioneer", ["nor", "sof"])  # cp deliberately omitted

    resp = client.get("/voyages/v_aegean_pioneer/evidence-checklist")
    assert resp.status_code == 200
    items = resp.json()["items"]
    cp_rows = [r for r in items if r["role"] == "cp_excerpt"]
    assert cp_rows, "demo fixture cites CP clauses, so cp_excerpt rows must exist"
    assert all(not r["attached"] for r in cp_rows)
