"""Pipeline orchestrator.

STUB for the backend-foundation PR: this returns the demo voyage fixture
(MT Aegean Pioneer, Rotterdam) without making any LLM calls. The real implementation will run Agents
1–4 (extraction -> classify+calculate -> dispute -> draft) and slot in here
behind the same signature, so call sites do not change.
"""

from __future__ import annotations

from .fixtures import demo_voyage_fixture
from .schemas import Perspective, VoyageState


async def run(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
) -> VoyageState:
    """Run the voyage pipeline and return the final ``VoyageState``.

    Args:
        voyage_id: Identifier assigned to this voyage.
        perspective: "owner" or "charterer".
        files: Raw uploaded PDF bytes keyed by document role
            ("cp", "nor", "sof"). Unused in the stub; the real pipeline runs
            these through pdfplumber + the agent fleet.

    Returns:
        A fully-populated ``VoyageState`` (stage="done").
    """
    # Real pipeline (later PR):
    #   text = {role: extract_pdf_text(blob) for role, blob in files.items()}
    #   extraction = await extractor.run(text, voyage_id, perspective)
    #   laytime, dispute = await asyncio.gather(
    #       calculator.run(extraction, perspective),
    #       analyst.run(extraction, perspective),
    #   )
    #   packet = await drafter.run(extraction, laytime, dispute, perspective)
    #   return VoyageState(..., stage="done", ...)
    return demo_voyage_fixture(voyage_id, perspective)
