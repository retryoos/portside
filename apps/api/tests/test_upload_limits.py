"""Tests for the P9 minimum slice: upload size + content-type allowlist.

POST /voyages must reject:
    - any file whose content-type is not application/pdf, with 415,
    - any file larger than ``MAX_UPLOAD_BYTES`` (25 MiB), with 413.

Both rejections happen before the background pipeline is fired, so no
``pipeline.run`` monkeypatch is needed for the failure cases. The happy
path test (a tiny PDF) does monkeypatch the pipeline so the FastAPI route
never reaches the real Anthropic SDK.

The existing 84,375 EUR gate (tests/test_calculator.py) is unaffected by
this module; calculator is read-only here.
"""

from __future__ import annotations

import io
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from laytimely_api import main as main_mod
from laytimely_api.limits import MAX_UPLOAD_BYTES
from laytimely_api.objects import LocalObjectStore
from laytimely_api.schemas import Perspective, VoyageState
from laytimely_api.storage import InMemoryStore, VoyageStore


@pytest.fixture(autouse=True)
def fresh_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> Iterator[InMemoryStore]:
    """Same pattern as test_main_async: fresh InMemoryStore + temp object
    store per test so the module-level singletons do not leak between
    tests."""
    store = InMemoryStore()
    monkeypatch.setattr(main_mod, "store", store)
    monkeypatch.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))  # type: ignore[arg-type]
    yield store


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(main_mod.app) as c:
        yield c


def _tiny_pdf() -> bytes:
    """A few bytes of valid-looking PDF header. pipeline.run is mocked so
    the content does not need to round-trip pdfplumber."""
    return b"%PDF-1.4 tiny"


def _good_files() -> dict[str, tuple[str, io.BytesIO, str]]:
    return {
        "cp": ("cp.pdf", io.BytesIO(_tiny_pdf()), "application/pdf"),
        "nor": ("nor.pdf", io.BytesIO(_tiny_pdf()), "application/pdf"),
        "sof": ("sof.pdf", io.BytesIO(_tiny_pdf()), "application/pdf"),
    }


def test_post_voyage_rejects_oversize_with_413(client: TestClient) -> None:
    """A 30 MiB upload on any slot must return 413 before the pipeline
    fires. Body content is irrelevant; only the byte count matters."""
    oversize = b"\x00" * (30 * 1024 * 1024)
    files = _good_files()
    files["sof"] = ("sof.pdf", io.BytesIO(oversize), "application/pdf")

    resp = client.post("/voyages", files=files, data={"perspective": "owner"})

    assert resp.status_code == 413, resp.text
    detail = resp.json()["detail"]
    assert "sof" in detail
    assert "25" in detail


def test_post_voyage_rejects_non_pdf_with_415(client: TestClient) -> None:
    """A .docx upload (or anything not in the allowlist) must return 415
    before the pipeline fires. The 415 response identifies the offending
    role so the UI can point at the right slot."""
    files = _good_files()
    docx_ctype = (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    files["cp"] = (
        "cp.docx",
        io.BytesIO(b"PK\x03\x04 fake docx"),
        docx_ctype,
    )

    resp = client.post("/voyages", files=files, data={"perspective": "owner"})

    assert resp.status_code == 415, resp.text
    detail = resp.json()["detail"]
    assert "cp" in detail
    assert "application/pdf" in detail


def test_post_voyage_accepts_small_pdf_happy_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The happy path must still return 201 and a well-formed voyage_id.
    Regression guard: the limits module must not break a normal upload."""

    async def fake_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: VoyageStore | None = None,
    ) -> VoyageState:
        state = VoyageState(
            voyage_id=voyage_id, perspective=perspective, stage="done"
        )
        if store is not None:
            await store.save(state)
        return state

    monkeypatch.setattr(main_mod.pipeline, "run", fake_pipeline)

    resp = client.post(
        "/voyages", files=_good_files(), data={"perspective": "owner"}
    )

    assert resp.status_code == 201, resp.text
    assert "voyage_id" in resp.json()


def test_at_the_limit_is_accepted(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file exactly at ``MAX_UPLOAD_BYTES`` must pass. The cap is
    inclusive at the limit and exclusive above it; this test pins that
    boundary so future refactors do not silently shift it."""

    async def fake_pipeline(
        voyage_id: str,
        perspective: Perspective,
        files: dict[str, bytes],
        store: VoyageStore | None = None,
    ) -> VoyageState:
        state = VoyageState(
            voyage_id=voyage_id, perspective=perspective, stage="done"
        )
        if store is not None:
            await store.save(state)
        return state

    monkeypatch.setattr(main_mod.pipeline, "run", fake_pipeline)

    at_limit = b"\x00" * MAX_UPLOAD_BYTES
    files = _good_files()
    files["sof"] = ("sof.pdf", io.BytesIO(at_limit), "application/pdf")

    resp = client.post("/voyages", files=files, data={"perspective": "owner"})

    assert resp.status_code == 201, resp.text
