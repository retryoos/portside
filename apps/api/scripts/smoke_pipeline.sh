#!/usr/bin/env bash
# End-to-end smoke for the Portside API + agent fleet.
#
# GATED — do not run until the user has authorized Anthropic API spend. This
# script POSTs the Rotterdam demo PDFs and lets the live pipeline run, which
# means an Anthropic API call per agent. Cost is ~$0.05–0.10 per run.
#
# Pre-reqs:
#   - apps/api/.env contains ANTHROPIC_API_KEY
#   - synthetic-data/generate.py has been run once to create the demo PDFs:
#       cd synthetic-data && pip install -r requirements.txt && python generate.py
#   - port 8000 is free
#
# Usage:
#   bash apps/api/scripts/smoke_pipeline.sh
#
# Pass criterion: final state has laytime.demurrage_due_usd == 84375 (the gate).

set -euo pipefail

# Resolve paths relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$API_DIR/../.." && pwd)"
PDFS_DIR="$REPO_ROOT/synthetic-data/scenarios/rotterdam-weather-dispute"
BASE_URL="http://localhost:8000"

UVICORN_PID=""
TMP_FILES=()

cleanup() {
  if [[ -n "${UVICORN_PID}" ]] && kill -0 "${UVICORN_PID}" 2>/dev/null; then
    kill "${UVICORN_PID}" 2>/dev/null || true
    wait "${UVICORN_PID}" 2>/dev/null || true
  fi
  for f in "${TMP_FILES[@]:-}"; do [[ -n "${f}" && -f "${f}" ]] && rm -f "${f}"; done
}
trap cleanup EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

json_field() {
  # Read a dotted field from a JSON file. Prefers jq; falls back to python3.
  local file="$1" path="$2"
  if command -v jq >/dev/null 2>&1; then
    jq -r ".${path}" "${file}"
  else
    PORTSIDE_JSON_PATH="${path}" python3 - "${file}" <<'PYEOF'
import json, os, sys
v = json.load(open(sys.argv[1]))
for k in os.environ["PORTSIDE_JSON_PATH"].split("."):
    v = v.get(k) if isinstance(v, dict) else None
print(v)
PYEOF
  fi
}

# 1. Sanity-check the demo PDFs exist.
for f in cp.pdf nor.pdf sof.pdf; do
  if [[ ! -f "${PDFS_DIR}/${f}" ]]; then
    fail "missing ${PDFS_DIR}/${f} — run: cd synthetic-data && python generate.py"
  fi
done

# 2. Boot uvicorn in the background from apps/api/.
echo "Booting uvicorn on :8000..."
(cd "${API_DIR}" && uv run uvicorn portside_api.main:app --port 8000) &
UVICORN_PID=$!

# 3. Wait up to 10s for /healthz to return 200.
for _ in $(seq 1 20); do
  if curl -sS -f "${BASE_URL}/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
if ! curl -sS -f "${BASE_URL}/healthz" >/dev/null 2>&1; then
  fail "API did not become healthy on ${BASE_URL}/healthz within 10s"
fi
echo "API healthy."

# 4. POST the three Rotterdam demo PDFs.
POST_BODY="$(mktemp)"; TMP_FILES+=("${POST_BODY}")
echo "POSTing voyage to ${BASE_URL}/voyages..."
curl -sS -f \
  -F "cp=@${PDFS_DIR}/cp.pdf;type=application/pdf" \
  -F "nor=@${PDFS_DIR}/nor.pdf;type=application/pdf" \
  -F "sof=@${PDFS_DIR}/sof.pdf;type=application/pdf" \
  -F "perspective=owner" \
  "${BASE_URL}/voyages" -o "${POST_BODY}" || fail "POST /voyages failed"

VOYAGE_ID="$(json_field "${POST_BODY}" voyage_id)"
[[ -z "${VOYAGE_ID}" || "${VOYAGE_ID}" == "None" ]] && fail "POST response missing voyage_id"
echo "voyage_id=${VOYAGE_ID}"

# 5. Poll GET /voyages/{voyage_id} every 500ms for up to 60s (=120 iterations).
STATE_BODY="$(mktemp)"; TMP_FILES+=("${STATE_BODY}")
final_stage=""
for _ in $(seq 1 120); do
  if curl -sS -f "${BASE_URL}/voyages/${VOYAGE_ID}" -o "${STATE_BODY}"; then
    final_stage="$(json_field "${STATE_BODY}" stage)"
    [[ "${final_stage}" == "done" || "${final_stage}" == "error" ]] && break
  fi
  sleep 0.5
done

if [[ "${final_stage}" != "done" ]]; then
  echo "--- final state ---" >&2
  cat "${STATE_BODY}" >&2 || true
  fail "voyage did not reach stage=done within 60s (final stage='${final_stage}')"
fi

# 6. Assert the gate: laytime.demurrage_due_usd == 84375.
QUANTUM="$(json_field "${STATE_BODY}" laytime.demurrage_due_usd)"
if [[ "${QUANTUM}" != "84375" && "${QUANTUM}" != "84375.0" && "${QUANTUM}" != "84375.00" ]]; then
  fail "demurrage_due_usd expected 84375, got '${QUANTUM}'"
fi

echo "PASS: voyage ${VOYAGE_ID} reached stage=done with demurrage_due_usd=${QUANTUM}"
exit 0
