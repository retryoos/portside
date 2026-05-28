#!/usr/bin/env bash
# Local dev server. --reload-dir limits the file watcher to the source package
# so it does NOT reload on every change inside .venv (uv installs there), which
# otherwise causes a reload storm. Override the port with PORT=8001 ./dev.sh
set -euo pipefail
cd "$(dirname "$0")"
exec uv run uvicorn portside_api.main:app --reload --reload-dir portside_api --port "${PORT:-8000}"
