"""Shared Anthropic client + structured-extraction helper for the agent fleet.

Model comes from ``ANTHROPIC_MODEL_PRIMARY`` (default Claude Sonnet 4.6, per
notes/03-agents.md). Opus 4.7 is the per-agent escape hatch — set the env var.
We use the SDK's structured-output path (``messages.parse`` with an
``output_format`` Pydantic model): the schema is derived from the model, the
response is validated, and ``parsed_output`` is a typed instance. The shared
system text is sent as a cache-eligible block so repeated calls hit the prompt
cache (notes/02-architecture.md §4).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

MODEL = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-6")

T = TypeVar("T", bound=BaseModel)


@lru_cache(maxsize=1)
def get_client() -> AsyncAnthropic:
    """Process-wide async client. Reads ANTHROPIC_API_KEY from the environment."""
    return AsyncAnthropic()


def cached_system(text: str) -> list[dict]:
    """A single system text block marked cache-eligible (ephemeral)."""
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


async def extract_structured(
    output_format: type[T],
    *,
    system: list[dict],
    user_text: str,
    max_tokens: int = 8192,
) -> T:
    """Run one structured-extraction call and return a validated model instance."""
    client = get_client()
    response = await client.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
        output_format=output_format,
    )
    if response.parsed_output is None:
        raise ValueError(
            f"structured extraction returned no parsed output "
            f"(stop_reason={response.stop_reason})"
        )
    return response.parsed_output
