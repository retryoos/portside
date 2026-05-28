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
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import pipeline, reviser
from .fixtures import seed_voyages
from .reviser import ReviseRequest, ReviseResponse
from .schemas import Perspective, VesselSummary, VoyageState, VoyageSummary
from .settings import settings
from .storage import InMemoryStore, VoyageStore

logger = logging.getLogger("portside_api")

app = FastAPI(title="Portside API", version="0.1.0")

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

# In-memory store, shared for the process lifetime.
store: VoyageStore = InMemoryStore()

# Hold strong references to in-flight background tasks. asyncio.create_task only
# weakly references its task, so without this the pipeline task can be GC'd /
# cancelled mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


@app.on_event("startup")
async def _seed_demo_voyages() -> None:
    """Populate the in-memory store with demo cases so the dashboard is never
    empty on a fresh process (notes: in-memory + startup seed; restart resets)."""
    for state in seed_voyages():
        await store.save(state)


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
