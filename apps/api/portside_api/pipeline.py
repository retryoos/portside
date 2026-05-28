"""Pipeline orchestrator.

Wires the real ingestion + calculation half (Agent 1 + Agent 2) over the
uploaded PDFs:

    pdfplumber text  ->  Agent 1 (extractor)  ->  Agent 2a classify + 2b arithmetic

Agent 2's track (analyst = Agent 3, drafter = Agent 4) plugs into the marked
SEAM below to fill `dispute` and `packet`. Until then the live path returns a
VoyageState with extraction + laytime populated; the offline demo fixture
(apps/web/lib/demo.ts) still carries the full packet for the UI.

Signature is unchanged so apps/api/.../main.py keeps working:
    state = await pipeline.run(voyage_id, perspective, files)
"""

from __future__ import annotations

from . import pdf
from .agents import calculator, extractor
from .fixtures import demo_voyage_fixture
from .schemas import Perspective, VoyageState


async def run(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
) -> VoyageState:
    """Run ingestion + calculation and return the VoyageState.

    `files` maps document role -> raw PDF bytes ({"cp", "nor", "sof"}).
    """
    texts = pdf.extract_all(files)

    # Demo safety net: if nothing extractable (e.g. placeholder upload, offline
    # smoke), serve the canonical demo voyage instead of erroring. Real demo PDFs
    # are text-native, so this only triggers on empty/garbage input.
    if not any(t.strip() for t in texts.values()):
        return demo_voyage_fixture(voyage_id, perspective)

    try:
        extraction = await extractor.run(texts, voyage_id, perspective)
        classifications = await calculator.classify_events(extraction, perspective)
        laytime = calculator.calculate_laytime(extraction, classifications)
    except Exception as exc:  # noqa: BLE001 — surface boundary failures honestly
        return VoyageState(
            voyage_id=voyage_id,
            perspective=perspective,
            stage="error",
            error=f"{type(exc).__name__}: {exc}",
        )

    dispute = None
    packet = None
    # ---- SEAM for Agent 2 (track-b) — fill dispute + packet here ----
    #   import asyncio; from .agents import analyst, drafter
    #   dispute = await analyst.run(extraction, laytime, perspective)
    #   packet  = await drafter.run(extraction, laytime, dispute, perspective)
    # Agent 3 (analyst) can run in parallel with any further Agent-2 work via
    # asyncio.gather; Agent 4 (drafter) awaits both. See notes/02-architecture.md §6.
    # ------------------------------------------------------------------

    return VoyageState(
        voyage_id=voyage_id,
        perspective=perspective,
        stage="done",
        extraction=extraction,
        laytime=laytime,
        dispute=dispute,
        packet=packet,
    )
