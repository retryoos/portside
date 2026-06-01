"""Tests for laytimely_api.settings — defaults, CORS parsing, .env loader.

No network calls. No Anthropic SDK use. We exercise the loader by monkeypatching
``_find_repo_root`` (or directly resetting ``_LOADED``) so each test gets a
clean filesystem view backed by ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from laytimely_api import settings as settings_module
from laytimely_api.settings import Settings, _parse_cors_origins


_TRACKED_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL_PRIMARY",
    "ANTHROPIC_MODEL_ESCAPE",
    "REQUEST_TIMEOUT_S",
    "CORS_ORIGINS",
)


@pytest.fixture(autouse=True)
def _clean_env_and_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts with a known-empty env + a fresh loader state."""
    for key in _TRACKED_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(settings_module, "_LOADED", False)
    # By default, point the loader at an empty tmp dir so import-time .env
    # files at the real repo root don't leak into individual tests.
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: None)


def test_defaults_when_env_is_empty() -> None:
    s = Settings.load()
    assert isinstance(s, Settings)
    assert s.anthropic_api_key is None
    assert s.model_primary == "claude-sonnet-4-6"
    assert s.model_escape == "claude-opus-4-7"
    assert s.request_timeout_s == 30.0
    assert s.cors_origins == ["http://localhost:3000"]


def test_cors_origins_parses_comma_separated_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com, https://b.com")
    s = Settings.load()
    assert s.cors_origins == ["https://a.com", "https://b.com"]


def test_cors_origins_empty_string_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "")
    s = Settings.load()
    assert s.cors_origins == ["http://localhost:3000"]


def test_parse_cors_origins_helper_drops_empties() -> None:
    assert _parse_cors_origins("a, , b,,c") == ["a", "b", "c"]
    assert _parse_cors_origins("") == []


def test_loader_does_not_raise_when_no_env_files_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_LOADED", False)
    monkeypatch.chdir(tmp_path)
    settings_module._load_dotenv_files_once()  # must not raise
    assert settings_module._LOADED is True


def test_repo_root_dotenv_is_parsed_into_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".env").write_text(
        "# a comment\n"
        "\n"
        "ANTHROPIC_MODEL_PRIMARY=from-dotenv\n"
        "REQUEST_TIMEOUT_S=42\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_LOADED", False)

    s = Settings.load()

    assert s.model_primary == "from-dotenv"
    assert s.request_timeout_s == 42.0


def test_apps_api_dotenv_is_also_parsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_dir = tmp_path / "apps" / "api"
    api_dir.mkdir(parents=True)
    (api_dir / ".env").write_text(
        "CORS_ORIGINS=https://only.example\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_LOADED", False)

    s = Settings.load()

    assert s.cors_origins == ["https://only.example"]


def test_existing_env_var_beats_dotenv_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_MODEL_PRIMARY", "X")
    (tmp_path / ".env").write_text(
        "ANTHROPIC_MODEL_PRIMARY=Y\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_LOADED", False)

    s = Settings.load()

    assert s.model_primary == "X"


def test_loader_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".env").write_text("REQUEST_TIMEOUT_S=11\n", encoding="utf-8")
    monkeypatch.setattr(settings_module, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_LOADED", False)

    settings_module._load_dotenv_files_once()
    assert settings_module._LOADED is True

    # Mutate the file; a second call must NOT re-read it.
    (tmp_path / ".env").write_text("REQUEST_TIMEOUT_S=99\n", encoding="utf-8")
    monkeypatch.delenv("REQUEST_TIMEOUT_S", raising=False)
    settings_module._load_dotenv_files_once()

    import os

    assert "REQUEST_TIMEOUT_S" not in os.environ
