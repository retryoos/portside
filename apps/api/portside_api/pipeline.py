"""Pipeline orchestrator.

Runs the full four-agent fleet over the uploaded PDFs:

    pdfplumber text -> Agent 1 (extractor) -> Agent 2a classify + 2b arithmetic
                    -> Agent 3 (analyst)   -> Agent 4 (drafter)

When a ``store`` is passed, the orchestrator persists an updated ``VoyageState``
at each stage transition (extracting -> calculating -> analyzing -> drafting ->
done) so the polling frontend can animate live progress (notes/02-architecture.md
§2). With ``store=None`` it runs synchronously and just returns the final state
(used by direct callers / tests). The signature stays back-compatible:
    state = await pipeline.run(voyage_id, perspective, files)
"""

from __future__ import annotations

from typing import Optional

from . import pdf
from .agents import analyst, calculator, drafter, extractor
from .fixtures import demo_voyage_fixture
from .schemas import (
    DisputeAnalysis,
    ExtractionResult,
    LaytimeResult,
    Perspective,
    PipelineStage,
    VoyageState,
)
from .storage import VoyageStore


async def run(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
    store: Optional[VoyageStore] = None,
) -> VoyageState:
    """Run the pipeline and return the final VoyageState.

    `files` maps document role -> raw PDF bytes ({"cp", "nor", "sof"}). If
    `store` is given, each stage is saved as it completes for live polling.
    """

    async def emit(
        stage: PipelineStage,
        *,
        extraction: ExtractionResult | None = None,
        laytime: LaytimeResult | None = None,
        dispute: DisputeAnalysis | None = None,
        packet=None,
        error: str | None = None,
    ) -> VoyageState:
        state = VoyageState(
            voyage_id=voyage_id,
            perspective=perspective,
            stage=stage,
            error=error,
            extraction=extraction,
            laytime=laytime,
            dispute=dispute,
            packet=packet,
        )
        if store is not None:
            await store.save(state)
        return state

    try:
        await emit("extracting")
        texts = pdf.extract_all(files)

        # Demo safety net: if nothing extractable (placeholder upload, offline
        # smoke), serve the canonical demo voyage instead of erroring. Real demo
        # PDFs are text-native, so this only triggers on empty input.
        if not any(t.strip() for t in texts.values()):
            state = demo_voyage_fixture(voyage_id, perspective)
            if store is not None:
                await store.save(state)
            return state

        extraction = await extractor.run(texts, voyage_id, perspective)

        await emit("calculating", extraction=extraction)
        classifications = await calculator.classify_events(extraction, perspective)
        laytime = calculator.calculate_laytime(extraction, classifications)

        await emit("analyzing", extraction=extraction, laytime=laytime)
        dispute = await analyst.run(extraction, laytime, perspective)

        await emit("drafting", extraction=extraction, laytime=laytime, dispute=dispute)
        packet = await drafter.run(extraction, laytime, dispute, perspective)
    except Exception as exc:  # noqa: BLE001 — surface boundary failures honestly
        return await emit("error", error=f"{type(exc).__name__}: {exc}")

    return await emit(
        "done",
        extraction=extraction,
        laytime=laytime,
        dispute=dispute,
        packet=packet,
    )
