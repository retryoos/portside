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

import logging
import os
from functools import lru_cache
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("portside_api")

MODEL = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-6")

# Opus 4.7 removed sampling params (temperature 400s); keep them for Sonnet/Opus
# 4.6 where temperature=0 makes structured extraction more deterministic.
_SEND_TEMPERATURE = "opus-4-7" not in MODEL

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
    max_attempts: int = 3,
) -> T:
    """Run a structured-extraction call and return a validated model instance.

    The SDK already retries network/429/5xx errors. This adds retries for the
    *content* failures that occasionally slip past structured decoding: a model
    degeneration that yields invalid JSON (e.g. a runaway out-of-range number) or
    an empty parse. Both are stochastic, so a fresh attempt usually succeeds.
    temperature=0 makes them rarer to begin with. A refusal is not retried.
    """
    client = get_client()
    extra: dict = {"temperature": 0} if _SEND_TEMPERATURE else {}

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.messages.parse(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_text}],
                output_format=output_format,
                **extra,
            )
        except ValidationError as exc:
            # Model emitted malformed/invalid JSON for the schema — retry fresh.
            last_error = exc
            logger.warning(
                "structured extraction parse failed for %s (attempt %d/%d): %s",
                output_format.__name__, attempt, max_attempts, exc,
            )
            continue

        if response.stop_reason == "refusal":
            raise ValueError(
                f"model refused structured extraction for {output_format.__name__}: "
                f"{response.stop_details}"
            )
        if response.parsed_output is None:
            # No parse (often max_tokens truncation) — retry.
            last_error = ValueError(
                f"no parsed output (stop_reason={response.stop_reason})"
            )
            logger.warning(
                "structured extraction empty for %s (attempt %d/%d, stop_reason=%s)",
                output_format.__name__, attempt, max_attempts, response.stop_reason,
            )
            continue

        return response.parsed_output

    raise ValueError(
        f"structured extraction for {output_format.__name__} failed after "
        f"{max_attempts} attempts: {last_error}"
    )
