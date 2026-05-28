"""Export the canonical demo VoyageState to apps/web/public/demo-fixture.json.

Run this whenever `apps/api/portside_api/fixtures.py` changes — the frontend's
offline-demo path reads this JSON file via a plain HTTP GET to /demo-fixture.json
(served as a static asset by Next.js out of `apps/web/public/`).

Usage:
    cd apps/api
    uv run python scripts/export_demo_fixture.py

The script is idempotent: same fixture in, same JSON out (modulo trailing newline).
No network. No Anthropic SDK call. Pure Python data dump.
"""

from __future__ import annotations

import sys
from pathlib import Path

from portside_api.fixtures import demo_voyage_fixture


def _output_path() -> Path:
    """Resolve `<repo_root>/apps/web/public/demo-fixture.json` from this file's
    location, regardless of the caller's CWD."""
    # apps/api/scripts/export_demo_fixture.py -> apps/api/scripts/ -> apps/api/ -> apps/ -> <repo_root>
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "apps" / "web" / "public" / "demo-fixture.json"


def export(out_path: Path | None = None) -> Path:
    """Write the canonical demo VoyageState as JSON, return the path written."""
    out_path = out_path or _output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    state = demo_voyage_fixture()
    # by_alias=True is REQUIRED: LaytimeRow exposes `from`/`to` as aliases over
    # the Python `from_ts`/`to_ts` reserved-keyword-safe field names. The wire
    # contract (apps/web/lib/types.ts) uses the aliases.
    json_text = state.model_dump_json(by_alias=True, indent=2)
    out_path.write_text(json_text + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    path = export()
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
