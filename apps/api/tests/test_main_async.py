"""Tests for the async-background POST /voyages pattern.

All tests monkeypatch ``portside_api.main.pipeline.run`` so the FastAPI route
never reaches the real Anthropic SDK. The critical invariant: POST returns
the voyage_id immediately and the pipeline runs in the background while the
frontend polls GET /voyages/{id} to watch the stage advance.
"""

from __future__ import annotations

import io
import re
import time
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from portside_api import main as main_mod
from portside_api.objects import LocalObjectStore
from portside_api.pipeline import GENERIC_PIPELINE_ERROR
from portside_api.schemas import Perspective, VoyageState
from portside_api.storage import InMemoryStore, VoyageStore

_VOYAGE_ID_RE = re.compile(r"^v_[0-9a-f]{12}$")


@pytest.fixture(autouse=True)
def fresh_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> Iterator[InMemoryStore]:
    """Swap a fresh InMemoryStore + a temp object store in for every test (the
    module-level singletons otherwise persist across tests and leak state /
    write PDFs into the package dir)."""
    store = InMemoryStore()
    monkeypatch.setattr(main_mod, "store", store)
    monkeypatch.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))  # type: ignore[arg-type]
    yield store


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(main_mod.app) as c:
        yield c


def _pdf_files() -> dict[str, tuple[str, io.BytesIO, str]]:
    """Junk PDF bytes — pipeline.run is mocked so content doesn't matter."""
    return {
        "cp": ("cp.pdf", io.BytesIO(b"%PDF-1.4 fake cp"), "application/pdf"),
        "nor": ("nor.pdf", io.BytesIO(b"%PDF-1.4 fake nor"), "application/pdf"),
        "sof": ("sof.pdf", io.BytesIO(b"%PDF-1.4 fake sof"), "application/pdf"),
    }


def _wait_until_terminal(
    client: TestClient, voyage_id: str, timeout_s: float = 2.0
) -> VoyageState:
    """Poll GET /voyages/{id} until stage is terminal (done|error) or timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = client.get(f"/voyages/{voyage_id}")
        assert resp.status_code == 200, resp.text
        state = VoyageState.model_validate(resp.json())
        if state.stage in {"done", "error"}:
            return state
        time.sleep(0.05)
    pytest.fail(
        f"voyage {voyage_id} did not reach a terminal stage within {timeout_s}s"
    )


def test_healthz_ok(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_post_voyage_returns_voyage_id_immediately(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST should return well before the (mocked) pipeline finishes."""
    import asyncio

    async def slow_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: VoyageStore | None = None,
    ) -> VoyageState:
        await asyncio.sleep(0.5)
        state = VoyageState(
            voyage_id=voyage_id, perspective=perspective, stage="done"
        )
        # The real pipeline persists staged states via `store`; main ignores the
        # return value, so the mock must save to be observable by GET polling.
        if store is not None:
            await store.save(state)
        return state

    monkeypatch.setattr(main_mod.pipeline, "run", slow_pipeline)

    start = time.monotonic()
    resp = client.post(
        "/voyages",
        files=_pdf_files(),
        data={"perspective": "owner"},
    )
    elapsed = time.monotonic() - start

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "voyage_id" in body
    assert _VOYAGE_ID_RE.match(body["voyage_id"]), body["voyage_id"]
    # The pipeline sleeps 0.5s; the POST should return in well under that.
    assert elapsed < 0.2, f"POST blocked for {elapsed:.3f}s — expected <0.2s"


def test_get_voyage_shows_initial_uploaded_stage(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An immediate GET after POST should see stage='uploaded' (the seed),
    then stage='done' once the background task settles."""
    import asyncio

    async def slow_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: VoyageStore | None = None,
    ) -> VoyageState:
        await asyncio.sleep(1.0)
        state = VoyageState(
            voyage_id=voyage_id, perspective=perspective, stage="done"
        )
        # The real pipeline persists staged states via `store`; main ignores the
        # return value, so the mock must save to be observable by GET polling.
        if store is not None:
            await store.save(state)
        return state

    monkeypatch.setattr(main_mod.pipeline, "run", slow_pipeline)

    resp = client.post(
        "/voyages", files=_pdf_files(), data={"perspective": "owner"}
    )
    assert resp.status_code == 201, resp.text
    voyage_id = resp.json()["voyage_id"]

    immediate = client.get(f"/voyages/{voyage_id}")
    assert immediate.status_code == 200
    assert immediate.json()["stage"] == "uploaded"

    final = _wait_until_terminal(client, voyage_id, timeout_s=2.0)
    assert final.stage == "done"


def test_get_voyage_404_for_unknown_id(client: TestClient) -> None:
    resp = client.get("/voyages/v_nonexistent")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "voyage not found"}


def test_pipeline_exception_records_error_state(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If pipeline.run raises an unexpected error, the background task records
    stage='error' with a generic message; internal exception type/message must
    NOT leak to the polled client state (verbose-error hardening)."""

    async def boom_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: VoyageStore | None = None,
    ) -> VoyageState:
        raise RuntimeError("boom")

    monkeypatch.setattr(main_mod.pipeline, "run", boom_pipeline)

    resp = client.post(
        "/voyages", files=_pdf_files(), data={"perspective": "owner"}
    )
    assert resp.status_code == 201, resp.text
    voyage_id = resp.json()["voyage_id"]

    final = _wait_until_terminal(client, voyage_id, timeout_s=2.0)
    assert final.stage == "error"
    assert final.error == GENERIC_PIPELINE_ERROR
    assert "boom" not in final.error
    assert "RuntimeError" not in final.error
