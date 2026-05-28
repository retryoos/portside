"""Agent 1 — Document Classifier & Extractor.

Takes pre-extracted text (pdfplumber) of the three voyage documents and returns
a single structured ExtractionResult. One Sonnet 4.6 call via the structured
output path. See notes/03-agents.md "Agent 1".
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import ExtractionResult, Perspective
from .llm import cached_system, extract_structured

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "extractor.md").read_text()


def _build_user_text(texts: dict[str, str]) -> str:
    """Concatenate the three document texts with neutral labels.

    The upstream role hints (cp/nor/sof) are NOT revealed — the model classifies
    from content, which keeps it honest (notes/03-agents.md).
    """
    parts: list[str] = []
    for i, (_, text) in enumerate(texts.items(), start=1):
        parts.append(f"=== DOCUMENT {i} ===\n{text.strip()}")
    return "\n\n".join(parts)


async def run(
    texts: dict[str, str],
    voyage_id: str,
    perspective: Perspective,
) -> ExtractionResult:
    """Classify + extract the three documents into an ExtractionResult."""
    system = cached_system(_PROMPT)
    user_text = _build_user_text(texts)
    return await extract_structured(
        ExtractionResult,
        system=system,
        user_text=user_text,
        max_tokens=8192,
    )
