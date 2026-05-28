"""FastAPI app + routes for the Portside backend.

Three endpoints:
    POST /voyages            upload CP/NOR/SoF PDFs, run pipeline, store state
    GET  /voyages/{id}       fetch the stored VoyageState
    GET  /healthz            liveness probe

No database, no auth — in-memory state, one process, for the demo.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import pipeline
from .schemas import Perspective, VoyageState
from .storage import InMemoryStore, VoyageStore

app = FastAPI(title="Portside API", version="0.1.0")

# CORS: the local Next.js dev server. The Amplify domain is added at deploy time.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store, shared for the process lifetime.
store: VoyageStore = InMemoryStore()

# Hold references to in-flight pipeline tasks so they are not garbage-collected
# mid-run (asyncio only keeps weak references to tasks).
_pipeline_tasks: set[asyncio.Task] = set()


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
    """Accept three voyage PDFs, kick off the pipeline, return the id immediately.

    The pipeline runs in the background and writes each stage to the store, so the
    frontend's GET poll sees progress (uploaded -> ... -> done | error).
    """
    files = {
        "cp": await cp.read(),
        "nor": await nor.read(),
        "sof": await sof.read(),
    }

    voyage_id = f"v_{uuid.uuid4().hex[:12]}"
    await store.save(
        VoyageState(voyage_id=voyage_id, perspective=perspective, stage="uploaded")
    )

    task = asyncio.create_task(pipeline.run(voyage_id, perspective, files, store))
    _pipeline_tasks.add(task)
    task.add_done_callback(_pipeline_tasks.discard)

    return {"voyage_id": voyage_id}


@app.get("/voyages/{voyage_id}")
async def get_voyage(voyage_id: str) -> VoyageState:
    """Return the stored VoyageState (the frontend polls this)."""
    state = await store.load(voyage_id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    return state
