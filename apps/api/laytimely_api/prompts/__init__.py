"""Prompt loading for the agent fleet.

Prompts live as `.md` files in this directory so they can be version-controlled
and iterated on without touching Python. Compose by concatenation:

    from laytimely_api.prompts import load_prompt
    SYSTEM = load_prompt("cross_cutting") + "\n\n" + load_prompt("analyst")

The cross-cutting prefix (notes/11-prompts.md "Cross-cutting rules") is shared
by every agent; role-specific prompts add to it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """Read and return the prompt text for `<name>.md` in this directory.

    Cached; safe to call from hot paths. Raises FileNotFoundError if the
    prompt file is missing (the .md filename is the contract).
    """
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
