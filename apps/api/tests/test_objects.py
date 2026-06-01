"""Tests for A3 object storage: the local object store, document metadata
records, the key invariant that uploaded documents survive a patch, and the
upload -> persist -> download path through the API.
"""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from laytimely_api import main as main_mod
from laytimely_api.db.engine import create_all, make_engine, make_sessionmaker
from laytimely_api.fixtures import demo_voyage_fixture
from laytimely_api.objects import LocalObjectStore, StoredDocument, build_key
from laytimely_api.schemas import Perspective, VoyageState
from laytimely_api.storage import InMemoryStore, SqlVoyageStore


def test_build_key_shape() -> None:
    assert build_key("v_1", "cp") == "voyages/v_1/cp.pdf"
    assert build_key("v_1", "nor", "prefix/") == "prefix/voyages/v_1/nor.pdf"


def test_local_object_store_round_trip(tmp_path: Path) -> None:
    async def go() -> tuple[bytes | None, bytes | None]:
        store = LocalObjectStore(tmp_path)
        await store.put("voyages/v_1/cp.pdf", b"%PDF-bytes", "application/pdf")
        got = await store.get("voyages/v_1/cp.pdf")
        missing = await store.get("voyages/v_1/missing.pdf")
        return got, missing

    got, missing = asyncio.run(go())
    assert got == b"%PDF-bytes"
    assert missing is None


def test_documents_survive_a_patch(tmp_path: Path) -> None:
    """The key A3 invariant: rewriting the voyage's analysis tree (save/patch)
    must NOT delete the uploaded document rows."""

    async def go() -> tuple[list[StoredDocument], VoyageState | None]:
        engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'd.db'}")
        await create_all(engine)
        store = SqlVoyageStore(make_sessionmaker(engine))
        await store.save(
            VoyageState(voyage_id="v_d", perspective="owner", stage="uploaded")
        )
        await store.record_documents(
            "v_d",
            [
                StoredDocument(
                    role="cp",
                    object_key="voyages/v_d/cp.pdf",
                    content_type="application/pdf",
                    size_bytes=10,
                )
            ],
        )
        # A staged pipeline patch that rewrites the tree...
        await store.patch("v_d", stage="done", extraction=demo_voyage_fixture().extraction)
        docs = await store.list_documents("v_d")
        reloaded = await store.load("v_d")
        await engine.dispose()
        return docs, reloaded

    docs, reloaded = asyncio.run(go())
    assert [d.role for d in docs] == ["cp"]  # survived the patch
    assert reloaded is not None and reloaded.stage == "done"
    assert reloaded.extraction is not None  # tree was updated


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    async def _noop_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: object | None = None,
    ) -> None:
        return None

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))
        mp.setattr(main_mod.pipeline, "run", _noop_pipeline)
        with TestClient(main_mod.app) as c:
            yield c


def _pdfs() -> dict[str, tuple[str, io.BytesIO, str]]:
    return {
        "cp": ("cp.pdf", io.BytesIO(b"%PDF cp bytes"), "application/pdf"),
        "nor": ("nor.pdf", io.BytesIO(b"%PDF nor"), "application/pdf"),
        "sof": ("sof.pdf", io.BytesIO(b"%PDF sof bytes longer"), "application/pdf"),
    }


def test_upload_persists_documents_and_downloads(client: TestClient) -> None:
    resp = client.post("/voyages", files=_pdfs(), data={"perspective": "owner"})
    assert resp.status_code == 201, resp.text
    voyage_id = resp.json()["voyage_id"]

    docs = client.get(f"/voyages/{voyage_id}/documents").json()
    assert sorted(d["role"] for d in docs) == ["cp", "nor", "sof"]
    cp_meta = next(d for d in docs if d["role"] == "cp")
    assert cp_meta["content_type"] == "application/pdf"
    assert cp_meta["size_bytes"] == len(b"%PDF cp bytes")

    download = client.get(f"/voyages/{voyage_id}/documents/cp")
    assert download.status_code == 200
    assert download.content == b"%PDF cp bytes"

    missing = client.get(f"/voyages/{voyage_id}/documents/xx")
    assert missing.status_code == 404
