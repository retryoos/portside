# Track B — AWS Deployment, Platform Ops & Edge Features (Panos)

> Your brief. The other two: [18 — Backend core & reasoning (dkall)](18-production-platform-dkall.md) ·
> [20 — Frontend (Roman)](20-production-frontend-roman.md). Read only this one.

**You own:** everything AWS / ops / deploy, plus the edge features that ride on it
(email/SES, Excel, hardening, observability). **Do P1 first** — provisioning the
cloud resources and publishing their identifiers is what *unblocks* dkall and Roman,
and provisioning empty resources depends on nobody's code, so you're never blocked.

## Shared rules (identical in all three briefs)
- **Subphase = one PR to `main`.** Small, disjoint file set, self-verifying. PRs merge in **any order or by cherry-pick**. No long-lived branch, nobody waits.
- **Build against contracts/mocks, never another track's running code.** Seams: `VoyageStore` Protocol, JWT claim contract (`sub` = user_id), `DATABASE_URL`, S3 bucket env, demo fixtures.
- **`schemas.py` / `web/lib/types.ts` are FROZEN.** New field = single author, announce first, mirror both sides.
- **Two gates never break:** owner `== 84375.0`; charterer `== 76875.0`. Offline `web/public/demo-fixture.json` always works.
- **Stack (AWS credits + sponsor):** Cognito · Aurora Serverless v2 Postgres · S3 · Doppler. Not Supabase/Clerk. **Deploy owned by you.**

## Contracts you PUBLISH early (this de-blocks the whole team)
The moment each resource exists, write its identifiers into a committed `.env.example`
+ the shared Doppler project. dkall and Roman build against these (or the `DEV_AUTH`
mock), so going live is an **env-only swap**.
- **Cognito User Pool** → issuer URL, JWKS URL, client ID(s), audience.
- **Aurora Serverless v2** → `DATABASE_URL`.
- **S3 bucket** → name + region.
- **Doppler project** → team access.

## Your subphase PRs (each → `main`, disjoint files)
- **P1 — Provision + publish contracts.** Stand up Cognito pool, Aurora v2, S3 bucket, Doppler project; commit `.env.example` with the keys; share Doppler. (Needs Roman **C0** = GitHub Education → Doppler free year; use a temp Doppler free tier until then.) *Accept:* team reads config from Doppler; Cognito JWKS reachable.
- **P2 — Secrets via Doppler.** Doppler CLI for local; Doppler integrations for App Runner + GitHub Actions; remove secrets from `.env` (keep `.env.example` as docs). *Accept:* app boots from Doppler; no secret in repo/history.
- **P3 — Backend deploy (App Runner).** Build/push image (ECR) or source-deploy via `apprunner.yaml`; env from Doppler; `CORS_ORIGINS` = Amplify domain. *Accept:* deployed `/healthz` → 200; live upload → done.
- **P4 — Frontend deploy (Amplify).** Connect repo, app root `apps/web`, `amplify.yml`; env `NEXT_PUBLIC_API_URL` + Cognito IDs; custom domain. *Accept:* Amplify URL renders; offline demo works cold.
- **P5 — CI/CD.** GitHub Actions: lint + `pytest` + `tsc` on PR; deploy on merge to `main`; Doppler service token. Files: `.github/workflows/*`.
- **P6 — Observability.** Sentry (API + web), CloudWatch 5xx alarm, structured logging, strip stray `print()`/`console.log`.
- **P7 — Email send (SES).** `POST /voyages/{id}/letter/email` (you own the SES creds). Files: `routes/email.py`. Consumes dkall A2 owner-scope via contract. Pairs Roman email button.
- **P8 — Excel export.** `openpyxl` → `/voyages/{id}/laytime.xlsx`. Files: `routes/exports.py`. Pairs Roman exports button.
- **P9 — API hardening.** Upload size/type limits, rate limiting, error taxonomy, pipeline timeout/retry audit.

> **Deploy isn't "last":** stand P3/P4 up against the **current `main`** early; once P5 CI is in, every merge redeploys automatically. So your deploy tracks `main` continuously rather than waiting for features to finish.

## Do NOT touch
`apps/api/portside_api/agents/*`, the `storage.py`/`auth.py` core (dkall — read the contract, don't edit). `apps/web/*` (Roman). `schemas.py` without announcing.

## Coordination (non-blocking)
P1 publish unblocks dkall A1/A2/A3 and Roman C2. P7/P8 ↔ Roman's email/exports buttons (agree the API shape in the PR).
