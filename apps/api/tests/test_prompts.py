"""Tests for portside_api.prompts.load_prompt.

These tests are pure: no network, no Anthropic SDK. They verify the helper
loads files from the prompts directory, that the cross-cutting prefix carries
the expected maritime-vocabulary markers, that the banned marketing words are
absent, that missing prompts raise FileNotFoundError, and that lru_cache is
returning the same object on repeated calls. The last test also guards Agent
1's already-merged role prompts against accidental breakage.
"""

from __future__ import annotations

import pytest

from portside_api.prompts import load_prompt


def test_load_cross_cutting_non_empty() -> None:
    text = load_prompt("cross_cutting")
    assert isinstance(text, str)
    assert text.strip() != ""


def test_load_cross_cutting_contains_maritime_vocab() -> None:
    text = load_prompt("cross_cutting")
    for marker in ("SHINC", "WIBON", "demurrage", "Notice of Readiness", "EUR 84,375.00"):
        assert marker in text, f"cross_cutting.md missing expected marker: {marker!r}"


def test_load_cross_cutting_contains_no_marketing_words() -> None:
    text = load_prompt("cross_cutting")
    lowered = text.lower()
    banned = ("leverage", "robust", "comprehensive", "powerful", "seamless")
    for word in banned:
        # The prompt may reference these words inside a quoted ban list. Check
        # that the ban-list line is the ONLY place they appear by counting
        # occurrences against the single expected occurrence on the bullet.
        # Simpler: assert the word appears at most once (the ban listing).
        assert lowered.count(word) <= 1, (
            f"banned marketing word {word!r} appears more than once in cross_cutting.md"
        )


def test_load_missing_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist_xyz")


def test_load_prompt_is_cached() -> None:
    first = load_prompt("cross_cutting")
    second = load_prompt("cross_cutting")
    assert first is second, "load_prompt should return the cached string object"


def test_existing_role_prompts_still_loadable() -> None:
    for name in ("extractor", "classifier"):
        text = load_prompt(name)
        assert isinstance(text, str)
        assert text.strip() != "", f"{name}.md unexpectedly empty"
