"""FastAPI app + routes for the Portside backend.

Endpoints:
    POST /voyages                 upload CP/NOR/SoF PDFs, kick off the pipeline in
                                  the background, return the voyage_id immediately
                                  so the frontend can poll for staged progress
                                  (notes/02-architecture.md §2).
    GET  /voyages/{id}            fetch the current VoyageState (polled ~500ms).
    POST /voyages/{id}/revise     inline-revise a letter/narrative segment
                                  (notes/13-inline-revision.md).
    GET  /healthz                 liveness probe.

No database, no auth — in-memory state, one process, for the demo.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import pipeline, reviser
from .db.engine import make_engine, make_sessionmaker, run_migrations
from .fixtures import seed_voyages
from .reviser import ReviseRequest, ReviseResponse
from .schemas import (
    Perspective,
    StatusUpdate,
    VesselSummary,
    VoyageState,
    VoyageSummary,
)
from .settings import settings
from .storage import SqlVoyageStore, VoyageStore

logger = logging.getLogger("portside_api")

# Relational store, shared for the process lifetime. The engine is lazy
# (no connection until first use), so constructing it at import is side-effect
# free; tests monkeypatch ``store`` with an InMemoryStore before startup.
_engine = make_engine(settings.database_url)
store: VoyageStore = SqlVoyageStore(make_sessionmaker(_engine))

# Hold strong references to in-flight background tasks. asyncio.create_task only
# weakly references its task, so without this the pipeline task can be GC'd /
# cancelled mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """On startup: migrate the schema (SQL backend only) and seed the demo cases
    if the store is empty. Seeding only-when-empty means a restart preserves real
    voyages instead of clobbering them (the point of persistence). Alembic spins
    up its own event loop, so run it off-thread to avoid nesting loops."""
    if isinstance(store, SqlVoyageStore):
        await asyncio.to_thread(run_migrations, settings.database_url)
    if not await store.list():
        for state in seed_voyages():
            await store.save(state)
    yield
    await _engine.dispose()


app = FastAPI(title="Portside API", version="0.1.0", lifespan=lifespan)

# CORS allowlist comes from settings.cors_origins (notes/02-architecture.md §12):
# local dev defaults to http://localhost:3000; add the Amplify domain on deploy
# via the CORS_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/voyages")
async def list_voyages() -> list[VoyageSummary]:
    """Return all voyages as lightweight summaries, newest-first (dashboard)."""
    return await store.list()


@app.get("/vessels")
async def list_vessels() -> list[VesselSummary]:
    """Return voyages grouped by vessel, newest-active first (vessels view)."""
    return await store.list_vessels()


@app.post("/voyages", status_code=201)
async def create_voyage(
    cp: UploadFile,
    nor: UploadFile,
    sof: UploadFile,
    perspective: Annotated[Perspective, Form()],
) -> dict[str, str]:
    """Accept three voyage PDFs, kick off the pipeline in the background, and
    return the voyage_id immediately. The pipeline writes each stage to the store
    so the frontend's GET poll sees progress (uploaded -> ... -> done | error).
    """
    files = {
        "cp": await cp.read(),
        "nor": await nor.read(),
        "sof": await sof.read(),
    }

    voyage_id = f"v_{uuid.uuid4().hex[:12]}"
    # Seed the initial state synchronously so a fast follow-up GET never 404s.
    await store.save(
        VoyageState(voyage_id=voyage_id, perspective=perspective, stage="uploaded")
    )
    # Fire-and-forget the pipeline; hold a strong reference until it completes.
    task = asyncio.create_task(_run_pipeline_bg(voyage_id, perspective, files))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

    return {"voyage_id": voyage_id}


@app.get("/voyages/{voyage_id}")
async def get_voyage(voyage_id: str) -> VoyageState:
    """Return the current VoyageState (the frontend polls this)."""
    state = await store.load(voyage_id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    return state


# Allowed human-driven lifecycle transitions once the pipeline is done. The
# claim then moves through negotiation: send it (-> pending), the charterer
# settles (-> settled) or rejects (-> rejected), and a rejected claim is revised
# and resent (-> pending). The pipeline stages (uploaded..drafting) are not in
# here — they advance on their own inside pipeline.run.
_NEXT_STAGES: dict[str, set[str]] = {
    "done": {"pending"},
    "pending": {"settled", "rejected"},
    "rejected": {"pending"},
}


@app.post("/voyages/{voyage_id}/status")
async def set_voyage_status(voyage_id: str, body: StatusUpdate) -> VoyageState:
    """Advance a voyage through the negotiation lifecycle (notes: status chips).

    Only the transitions in ``_NEXT_STAGES`` are permitted; anything else is a
    409 so the UI can't drive the claim into an inconsistent state.
    """
    state = await store.load(voyage_id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")

    allowed = _NEXT_STAGES.get(state.stage, set())
    if body.stage not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"cannot move from '{state.stage}' to '{body.stage}'",
        )

    updated = await store.patch(voyage_id, stage=body.stage)
    assert updated is not None  # load() above proved it exists
    return updated


@app.post("/voyages/{voyage_id}/revise")
async def revise_voyage(voyage_id: str, body: ReviseRequest) -> ReviseResponse:
    """Inline-revise a letter/narrative segment (notes/13-inline-revision.md).

    The rewrite is validated server-side: if it changed a monetary value or
    dropped a CP clause / SoF event reference, it is rejected with HTTP 422 and
    the safety report so the UI can surface why.
    """
    state = await store.load(voyage_id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")

    blocked, response = await reviser.revise(body, state)
    if blocked:
        raise HTTPException(status_code=422, detail=response.model_dump())
    return response


async def _run_pipeline_bg(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
) -> None:
    """Run the pipeline in the background.

    The pipeline saves each stage to the store as it advances (live polling) and
    records stage="error" internally on failure. Passing `store` is what enables
    the staged saves. This wrapper is a belt-and-suspenders guard for anything
    that escapes the pipeline's own handler (notes/02-architecture.md §7).
    """
    try:
        await pipeline.run(voyage_id, perspective, files, store)
    except Exception as exc:  # noqa: BLE001 - boundary handler
        logger.exception("pipeline failed for voyage %s", voyage_id)
        await store.save(
            VoyageState(
                voyage_id=voyage_id,
                perspective=perspective,
                stage="error",
                error=f"{type(exc).__name__}: {exc}",
            )
        )
