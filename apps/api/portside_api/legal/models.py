"""Wire models for the legal citation subsystem.

Feature-local: lives next to the tools so the frozen schemas.py stays
untouched. Agents that emit a ``cited_authorities`` field embed
``CitedAuthority`` directly in their feature-local output models (analyst
sub-scores, EU ETS / FuelEU compliance reports, etc.). See
notes/architecture_weeks_5_to_8.md §1.6.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Tool channels through which an authority can be verified. New channels
# require a code change (the verifier matches on this literal); a new tool
# without a matching channel here is dropped.
ToolChannel = Literal["corpus", "lookup", "eur_lex", "imo", "bailii"]


class CitedAuthority(BaseModel):
    """One legal authority cited in agent output.

    Verification contract: ``verified_via_tool`` MUST be True for the route
    layer to accept the field. ``verify.validate_authorities`` runs after the
    LLM call against the recorded tool transcript and silently drops any
    authority whose ``citation`` did not appear in a tool result. The model is
    told this in its system prompt; if it cheats, the schema layer rejects.
    """

    citation: str = Field(..., min_length=2)
    verified_via_tool: bool
    tool_used: ToolChannel
    proposition: str = Field(
        ..., description="One-line summary of what the authority supports."
    )
    url: Optional[str] = None


# ---------------------------------------------------------------------------
# Corpus row + search hit
# ---------------------------------------------------------------------------


class CorpusEntry(BaseModel):
    """One row of the curated case-law JSONL.

    `case_id` is a stable slug used as the primary key. `topics` are short
    lowercase tags (e.g. "weather_exception", "notice_of_readiness") used by
    the BM25 search to bias toward the topic the analyst is reasoning about.
    """

    case_id: str
    citation: str
    court: str
    year: int
    topics: list[str]
    headnote: str
    url: Optional[str] = None
    full_text_free: bool = False


class CaseHit(BaseModel):
    """One result from ``search_case_corpus``."""

    case_id: str
    citation: str
    headnote: str
    url: Optional[str] = None
    score: float


# ---------------------------------------------------------------------------
# IMO conventions (public-domain texts shipped in the repo)
# ---------------------------------------------------------------------------


class ConventionArticle(BaseModel):
    """One numbered article (or rule) inside an IMO convention.

    `name` is the convention slug (e.g. "hague_visby"). `article` is the human
    citation token (e.g. "III r 6"). `text` is the verbatim public-domain text.
    """

    name: str
    article: str
    text: str
    url: Optional[str] = None
