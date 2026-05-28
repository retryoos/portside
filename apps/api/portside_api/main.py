"""FastAPI app + routes for the Portside backend.

Three endpoints:
    POST /voyages            upload CP/NOR/SoF PDFs, kick off the pipeline in the
                             background, return the voyage_id immediately so the
                             frontend can begin polling for staged progress
                             (notes/02-architecture.md §2).
    GET  /voyages/{id}       fetch the current VoyageState (the frontend polls
                             this every 500ms).
    GET  /healthz            liveness probe.

No database, no auth — in-memory state, one process, for the demo.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import pipeline
from .schemas import Perspective, VoyageState
from .settings import settings
from .storage import InMemoryStore, VoyageStore

logger = logging.getLogger("portside_api")

app = FastAPI(title="Portside API", version="0.1.0")

# CORS allowlist comes from settings.cors_origins (notes/02-architecture.md §12):
# - local dev: "http://localhost:3000" is the default
# - AWS deploy: add the Amplify domain via the CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store, shared for the process lifetime.
store: VoyageStore = InMemoryStore()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/voyages", status_code=201)
async def create_voyage(
    cp: UploadFile,
    nor: UploadFile,
    sof: UploadFile,
    perspective: Annotated[Perspective, Form()],
) -> dict[str, str]:
    """Accept three voyage PDFs, kick off the pipeline in the background, return
    the voyage_id immediately. The frontend polls GET /voyages/{id} to watch the
    stage advance (notes/02-architecture.md §2).
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
    # Fire-and-forget the pipeline. We hold a reference so the task is not GC'd
    # mid-flight (asyncio.create_task only weakly references its task object).
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


# Hold strong references to in-flight background tasks. asyncio.create_task
# returns a task that is otherwise weakly referenced by the event loop, so
# without a strong ref the task may be cancelled mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


async def _run_pipeline_bg(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
) -> None:
    """Run the pipeline in the background and write the result to the store.

    On any unexpected exception we record stage="error" with the message and
    return, so the polling frontend sees a terminal state and can render it
    (notes/02-architecture.md §7).
    """
    try:
        state = await pipeline.run(voyage_id, perspective, files)
        await store.save(state)
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
