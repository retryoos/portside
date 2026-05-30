# Track B — AWS Deployment, Platform Ops & Edge Features (Panos)

> Your brief. The other two: [18 — Backend core & reasoning (dkall)](18-production-platform-dkall.md) ·
> [20 — Frontend (Roman)](20-production-frontend-roman.md). Read only this one.
>
> **Current priority order:** [first_customer_checklist.md §10](first_customer_checklist.md#10-ranked-subphase-order).
> Read that first — it supersedes the ordering implied below. Subphase content
> is unchanged; only the sequencing and the tier each one belongs to.

**You own:** everything ops / deploy, plus the edge features that ride on it
(email/SES, Excel, hardening, observability). Until we have a paying customer
we deploy the frontend on **Vercel Hobby** (free, GitHub auto-deploy) and the
backend on **AWS App Runner**. AWS provisioning of Cognito / Aurora / S3 / SES
waits for the first customer; provisioning empty resources depends on nobody's
code, so when you do start P1 you are never blocked.

## Shared rules (identical in all three briefs)
- **Subphase = one PR to `main`.** Small, disjoint file set, self-verifying. PRs merge in **any order or by cherry-pick**. No long-lived branch, nobody waits.
- **Build against contracts/mocks, never another track's running code.** Seams: `VoyageStore` Protocol, JWT claim contract (`sub` = user_id), `DATABASE_URL`, S3 bucket env, demo fixtures.
- **`schemas.py` / `web/lib/types.ts` are FROZEN.** New field = single author, announce first, mirror both sides.
- **Two gates never break:** owner `== 84375.0`; charterer `== 76875.0`. Offline `web/public/demo-fixture.json` always works.
- **Stack:** Vercel (pre-customer frontend) + AWS App Runner (backend, both phases). On first customer: Cognito · Aurora Serverless v2 Postgres · S3 · Doppler. AWS Amplify hosting is **optional** even on first customer (Vercel is a fine permanent home unless AWS-native is a hard requirement).

## Contracts you PUBLISH early (this de-blocks the whole team)
The moment each resource exists, write its identifiers into a committed `.env.example`
+ the shared Doppler project. dkall and Roman build against these (or the `DEV_AUTH`
mock), so going live is an **env-only swap**.
- **Cognito User Pool** → issuer URL, JWKS URL, client ID(s), audience.
- **Aurora Serverless v2** → `DATABASE_URL`.
- **S3 bucket** → name + region.
- **Doppler project** → team access.

## Your subphase PRs (each → `main`, disjoint files)

The PRs themselves are the same; only the order and tier label changed. See the
[checklist](first_customer_checklist.md#10-ranked-subphase-order) for the full
tier breakdown.

- **P0 — Vercel frontend deploy (Tier 0, NEW, do first).** Connect `apps/web` to Vercel Hobby. Env: `NEXT_PUBLIC_API_URL` = your App Runner URL, `AUTH_SECRET` = HMAC secret for the cookie stub. `admin / admin` stays on (`DEV_AUTH=1` on the API). *Accept:* public URL renders the dashboard, login with admin/admin works, an upload reaches the live App Runner backend.
- **P3 — Backend deploy (App Runner) (Tier 0).** Build/push image (ECR) or source-deploy via `apprunner.yaml`; env directly on App Runner (no Doppler yet); `CORS_ORIGINS` = the Vercel URL. *Accept:* deployed `/healthz` → 200; live upload → done.
- **P9 (minimum slice) — basic limits (Tier 0).** Upload size cap (25 MB) + `application/pdf` content-type allowlist on `POST /voyages`. The full hardening is a Tier 2 follow-up.
- **P6 (minimum slice) — Sentry on API + web (Tier 0).** Smallest possible install on both apps. CloudWatch alarms wait for Tier 2.
- **P1 — Provision + publish contracts (Tier 1, on first customer).** Stand up Cognito pool, Aurora v2, S3 bucket, Doppler project; fill in `.env.example` with the real IDs; share Doppler. (Needs Roman **C0** = GitHub Education → Doppler free year; use a temp Doppler free tier until then.) *Accept:* team reads config from Doppler; Cognito JWKS reachable.
- **P2 — Secrets via Doppler (Tier 1).** Doppler CLI for local; Doppler integrations for App Runner + Vercel + GitHub Actions; remove secrets from App Runner/Vercel env panels (keep `.env.example` as docs). *Accept:* both apps boot from Doppler; no secret in repo/history.
- **P9 (full) — API hardening (Tier 2, before billing).** Rate limiting on `POST /api/auth/login` + `POST /voyages`, error taxonomy, pipeline timeout/retry audit, DB backup policy.
- **P5 — CI/CD (Tier 2, before billing).** GitHub Actions: lint + `pytest` + `tsc` on PR; deploy on merge to `main`; Doppler service token. Files: `.github/workflows/*`.
- **P6 (full) — Observability (Tier 2, before billing).** Full Sentry (release tagging, source maps), CloudWatch 5xx alarm to ops email, structured logging, strip any stray `print()`/`console.log`.
- **P4 — Frontend deploy on Amplify (Tier 3, optional).** Only if AWS-native frontend hosting becomes a hard requirement (compliance, single-bill, VPC). Otherwise Vercel stays as the permanent home. Connect repo, app root `apps/web`, `amplify.yml`; env `NEXT_PUBLIC_API_URL` + Cognito IDs; custom domain. *Accept:* Amplify URL renders; offline demo works cold.
- **P7 — Email send (SES) (Tier 3, customer-driven).** `POST /voyages/{id}/letter/email`. Files: `routes/email.py`. Consumes dkall A2 owner-scope via contract. Pairs Roman email button.
- **P8 — Excel export (Tier 3, customer-driven).** `openpyxl` → `/voyages/{id}/laytime.xlsx`. Files: `routes/exports.py`. Pairs Roman exports button.

> **Deploy isn't "last":** stand P0/P3 up against the **current `main`** now; once P5 CI is in, every merge redeploys automatically. So your deploy tracks `main` continuously rather than waiting for features to finish.

## Do NOT touch
`apps/api/portside_api/agents/*`, the `storage.py`/`auth.py` core (dkall — read the contract, don't edit). `apps/web/*` (Roman). `schemas.py` without announcing.

## Coordination (non-blocking)
P0/P3 are independent and can land in parallel (the Vercel URL just needs the App Runner URL set as `NEXT_PUBLIC_API_URL`). P1 publish unblocks dkall A1/A2/A3 and Roman C2. P7/P8 ↔ Roman's email/exports buttons (agree the API shape in the PR).
