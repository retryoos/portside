# Track A — Backend Core & Reasoning (dkall)

> Your brief. The other two: [19 — AWS deploy/ops/edge (Panos)](19-production-reasoning-panos.md) ·
> [20 — Frontend (Roman)](20-production-frontend-roman.md). Read only this one.

**You own:** the backend application code — the data / auth-verifier / object-storage
adapters and the two reasoning demo beats. **You do NOT own AWS provisioning or
deploy** (that's Panos). You build against the env contract he publishes, or local
fallbacks, so you never wait on him.

## Shared rules (identical in all three briefs)
- **Subphase = one PR to `main`.** Small, disjoint file set, self-verifying (a test or smoke). PRs merge in **any order or by cherry-pick** — your "track" is just the sum of your subphase PRs. No long-lived branch, nobody waits.
- **Build against contracts/mocks, never another track's running code.** Shared seams: the `VoyageStore` Protocol, the JWT claim contract (`sub` = user_id), `DATABASE_URL`, the S3 bucket env, the demo fixtures.
- **`schemas.py` / `web/lib/types.ts` are FROZEN.** New field = single author, announce first, mirror both sides.
- **Two gates never break:** owner `demurrage_due_eur == 84375.0`; charterer rebuttal `== 76875.0`. Offline `web/public/demo-fixture.json` always works.
- **Stack (AWS credits + sponsor):** Cognito · Aurora Serverless v2 Postgres · S3 · Doppler. Not Supabase/Clerk. **Deploy owned by Panos.**

## Contracts you consume (so you're never blocked)
- `VoyageStore` Protocol — you implement `PostgresStore` behind it.
- **JWT:** `sub` = user_id; issuer / JWKS / audience come from env (Panos publishes the Cognito pool). Until then, a `DEV_AUTH=1` stub verifier returns a fixed dev user.
- `DATABASE_URL` — build on local **SQLite**; the Aurora URL slots in later by env only.
- S3 bucket env — local `/tmp` fallback until the bucket exists.

## Your subphase PRs (each → `main`, disjoint files)
- **A1 — Persistence.** `SQLiteStore` → `PostgresStore` behind `VoyageStore`; SQLAlchemy + Alembic; add `owner_user_id` to `VoyageState`. Files: `storage.py`, `db/`, `alembic/`, `tests/test_storage.py`. *Accept:* restart-safe; tests green on SQLite.
- **A2 — Auth verifier.** Cognito JWT FastAPI dependency (JWKS/issuer/aud from env; `DEV_AUTH` stub); owner-scope `/voyages` list+read+delete; add `GET /me`, `DELETE /voyages/{id}`. Files: `auth.py`, `main.py`. *Accept:* unauthed → 401; `DEV_AUTH` path runs offline; real pool is env-only swap.
- **A3 — S3 object storage.** Adapter; uploads to the env bucket with local fallback; keys on the voyage; pipeline reads from it. Files: `objects.py`, `main.py` upload path. *Accept:* PDFs reload-safe; works with no AWS via fallback.
- **A4 — Multi-instance progress.** Ensure the background pipeline writes each staged update to the store (not memory) — the real fix behind the "no Redis" call. Files: `pipeline.py` wiring. *Accept:* progress readable from a second process.
- **A5 — Edit-with-AI persist (pairs Roman C1).** Endpoint to write an *accepted* revision into the stored `ClaimPacket` markdown, so edits survive reload + reach the PDF. Files: `main.py` route, store patch. *Accept:* accept → reload → persists → in exported PDF.
- **A6 — Both sides of the deal (pairs Roman C4).** `POST /voyages/{id}/rebut` → charterer packet (`Perspective="charterer"` + `charterer_argument` already exist); deterministic swing **84,375.00 → 76,875.00** (4h × 1,875). **Lock 76,875.00 in `tests/test_rebut.py`.** Files: `main.py`/route, `agents/analyst.py` (param). *Accept:* test asserts 76,875.00; owner gate untouched.
- **A7 — Research agents (pairs Roman C3).** Tool-using evidence agent filling the unused `FlaggedEvent.evidence_required`; committed Rotterdam fixture for offline; live API behind a flag. Files: `agents/evidence.py`, `prompts/evidence.md`, fixture. *Accept:* offline run returns sourced evidence per disputed hour.

## Do NOT touch
`apps/web/*`, deploy/infra (`apprunner.yaml`, `amplify.yml`, `.github/`) — Panos/Roman. `schemas.py` without announcing.

## Coordination (contract-mediated, non-blocking)
Publish each route's request/response in the PR description. A5↔C1 (accept payload), A6↔C4 (rebut shape), A7↔C3 (evidence shape).
