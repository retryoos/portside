"""Feature-local wire models for analyst citations (W0/W5, §1.6).

Lives outside ``agents/analyst.py`` so storage, route, and test modules can
import the wire shapes without dragging the LLM client and the prompt file
load at module import time. The ``agents.analyst`` module re-exports both
names so callers can continue to import from there.
"""

from __future__ import annotations

from pydantic import BaseModel

from .legal.models import CitedAuthority
from .schemas import DisputeAnalysis


class FlaggedEventCitations(BaseModel):
    """Per-flagged-event citation bundle.

    Sibling to the existing ``DisputeAnalysis.flagged_events`` list keyed by
    ``event_id`` so the frozen ``FlaggedEvent`` schema is untouched.
    """

    event_id: str
    cited_authorities: list[CitedAuthority]


class EnrichedDisputeAnalysis(BaseModel):
    """``DisputeAnalysis`` plus the verified citations per flagged event."""

    analysis: DisputeAnalysis
    citations: list[FlaggedEventCitations]
