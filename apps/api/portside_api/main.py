"""FastAPI app + routes for the Portside backend.

Three endpoints:
    POST /voyages            upload CP/NOR/SoF PDFs, run pipeline, store state
    GET  /voyages/{id}       fetch the stored VoyageState
    GET  /healthz            liveness probe

No database, no auth — in-memory state, one process, for the demo.
"""

from __future__ import annotations

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
    """Accept three voyage PDFs, run the pipeline, store the result."""
    files = {
        "cp": await cp.read(),
        "nor": await nor.read(),
        "sof": await sof.read(),
    }

    voyage_id = f"v_{uuid.uuid4().hex[:12]}"
    state = await pipeline.run(voyage_id, perspective, files)
    await store.save(state)

    return {"voyage_id": voyage_id}


@app.get("/voyages/{voyage_id}")
async def get_voyage(voyage_id: str) -> VoyageState:
    """Return the stored VoyageState (the frontend polls this)."""
    state = await store.load(voyage_id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    return state
