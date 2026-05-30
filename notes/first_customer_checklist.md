# First customer migration checklist

> Going from the local laptop demo (`admin/admin`, SQLite, filesystem objects, no
> deploy) to a live URL ready for the first paying customer. The product code is
> unchanged: this is a configuration, provisioning and deploy exercise.
>
> Cross-references:
> [21-authentication-stub.md](21-authentication-stub.md) ·
> [18-production-platform-dkall.md](18-production-platform-dkall.md) ·
> [19-production-reasoning-panos.md](19-production-reasoning-panos.md) ·
> [20-production-frontend-roman.md](20-production-frontend-roman.md).

---

## 0. Prerequisites

| Item | Why | Owner |
| --- | --- | --- |
| AWS account with billing + IAM admin | Cognito, RDS, S3, App Runner, SES, CloudWatch | Panos |
| AWS credits (sponsor or Activate Founders) | Aurora v2 is not free | Panos |
| Domain (e.g. `papership.ai`) | Custom domain on the chosen frontend host + SES sender | Panos |
| Doppler workspace | Single source of truth for secrets | Roman (via GitHub Education) |
| GitHub admin on `retryoos/portside` | Service tokens, branch protections | Roman |
| Sentry org (free tier OK) | API + web error reporting | Panos |
| ANTHROPIC_API_KEY for prod | Already in use locally; cycle for prod | Panos |
| Vercel account (free Hobby tier) | Pre-customer demo frontend | Roman |

---

## 0.5 Phasing: pre-customer demo vs first customer

Two distinct deploys, two different toolchains. The product code is the same;
the surrounding infrastructure differs.

### Pre-customer demo (now)

- **Frontend:** Vercel Hobby tier. Free, instant GitHub deploys, ~/.vercel/project
  for env vars. Connect `apps/web`, set `NEXT_PUBLIC_API_URL` to the App Runner
  URL, done.
- **Backend:** AWS App Runner (Panos **P3**). Build from `apps/api/Dockerfile`
  via `apprunner.yaml`. Public `/healthz`.
- **Auth:** keep the `admin / admin` stub. `DEV_AUTH=1` on the backend. No
  Cognito provisioned yet.
- **Database:** SQLite (current default) is enough for a demo. If we want the
  demo data to survive backend restarts, provision a small RDS instance early
  and point `DATABASE_URL` at it; otherwise stay on SQLite.
- **Object storage:** filesystem on App Runner's ephemeral disk is fine for a
  demo. Voyage PDFs are not durable across restarts; that is acceptable until
  a real customer arrives.
- **Secrets:** raw env vars in App Runner + Vercel are acceptable for the demo.
  Doppler is preferable but not blocking.
- **Goal:** a public URL good enough to send to an investor or a prospect.

### First paying customer (later)

- **Frontend:** decide: stay on Vercel and attach the custom domain, or migrate
  to AWS Amplify (Panos **P4**) for AWS-native ops. Vercel works long-term; the
  Amplify migration is only worth doing if AWS-native is a hard requirement
  (compliance, single-bill, VPC integration).
- **Backend:** same App Runner service. Flip `DEV_AUTH=0`.
- **Auth:** Cognito User Pool (**P1**). Frontend auth swap (Section 4 below).
- **Database:** Aurora Serverless v2 (**P1**). `alembic upgrade head`.
- **Object storage:** S3 (**P1**).
- **Secrets:** Doppler (**P2**) is mandatory before any real keys touch
  production.
- **Hardening, CI/CD, observability:** required before billing (**P9**,
  **P5**, **P6**).

---

## 1. Provisioning order (each step is independent once the one before it lands)

Cognito and S3 can be provisioned in any order; RDS must exist before the first
`alembic upgrade head`; Doppler must exist before secrets stop living on
laptops.

### 1a. Cognito User Pool

- Provision User Pool with email as the alias attribute, password policy
  (`min 12, mixed case, digit, symbol`), MFA optional for first customer.
- Create an App Client (no client secret if the UI is a SPA, with secret if the
  Next.js server brokers the InitiateAuth call - the latter is what
  [21-authentication-stub.md §9.1](21-authentication-stub.md#91-swap-to-aws-cognito-planned-for-c2-second-half) assumes).
- Record and commit to `.env.example`:
  - `COGNITO_REGION`
  - `COGNITO_USER_POOL_ID`
  - `COGNITO_CLIENT_ID`
  - `COGNITO_ISSUER` (= `https://cognito-idp.{region}.amazonaws.com/{pool_id}`)
  - `COGNITO_JWKS_URL` (= `{issuer}/.well-known/jwks.json`)
- Backend (`apps/api/portside_api/auth.py`) is already wired: setting these
  plus `DEV_AUTH=0` turns on real verification. No backend code change.

### 1b. RDS Aurora Serverless v2 Postgres

- Provision a single cluster, `db.serverless` writer, min ACU 0.5 / max ACU 4
  for the first customer.
- Subnet group across at least two AZs, security group allowing the App Runner
  service's VPC connector (or a public endpoint with strict IP allowlist during
  bring-up only).
- Create the application user (not the master) and a database `papership`.
- Compose `DATABASE_URL` in the asyncpg form:
  `postgresql+asyncpg://{user}:{password}@{endpoint}:5432/papership`.
- `apps/api/portside_api/db/engine.py` and `apps/api/portside_api/settings.py`
  read `DATABASE_URL` directly; production override is one env var.

### 1c. S3 bucket

- Bucket `papership-voyages-prod-{region}`. Block public access. Default
  server-side encryption with SSE-S3 (or SSE-KMS with a customer-managed key
  if compliance demands it).
- Lifecycle rule: transition to `STANDARD_IA` after 30 days; no auto-delete.
- IAM role for App Runner with `s3:PutObject` and `s3:GetObject` only on
  `papership-voyages-prod-*/voyages/*`.
- Record:
  - `S3_BUCKET`
  - `S3_REGION`
  - (optional) `S3_PREFIX`
- `apps/api/portside_api/objects.py` switches to `S3ObjectStore`
  automatically when `S3_BUCKET` is set. No code change.

### 1d. Doppler

- Create the `papership` project with three configs: `dev`, `staging`, `prod`.
- Move every value from `apps/api/.env` and `apps/web/.env` into Doppler.
- Service tokens: one for App Runner (`apprunner-prod`), one for Amplify
  (`amplify-prod`), one for GitHub Actions (`ci-prod`, read-only).
- Local laptops use `doppler run` instead of `.env` files. Keep
  `.env.example` committed as documentation; nothing else in `.env*`.

---

## 2. Database migration

```
doppler run --config prod -- alembic -c apps/api/alembic.ini upgrade head
```

This applies the three existing migrations:
- `77986f4b9f2d_initial_schema`
- `3e1ee1f39a0c_voyage_documents`
- `f555fafd0771_voyage_evidence`

Smoke-check: `psql ... -c "select count(*) from voyages;"` returns `0`.

---

## 3. Backend deploy (App Runner)

- Build from `apps/api/Dockerfile`, push to ECR, or source-deploy via
  `apps/api/apprunner.yaml`.
- Env from Doppler: every key in `apps/api/.env.example` plus `DEV_AUTH=0` and
  `CORS_ORIGINS=https://app.papership.ai` (the Amplify custom domain).
- Health check: `/healthz` returns `{"status":"ok"}`.
- Manual smoke: `curl https://api.papership.ai/healthz`.

---

## 4. Frontend auth swap (the one code change)

The stub is engineered so this is a two-file change. See
[21-authentication-stub.md §9.1](21-authentication-stub.md#91-swap-to-aws-cognito-planned-for-c2-second-half).

1. Replace `apps/web/lib/auth/credentials.ts` with a Cognito `InitiateAuth`
   call (USER_PASSWORD_AUTH for first customer simplicity; rotate to
   USER_SRP_AUTH later). On success, return the `IdToken`.
2. Replace `apps/web/lib/auth/session.ts` with a JWKS-backed verifier
   (`jose.createRemoteJWKSet(COGNITO_JWKS_URL)` + `jose.jwtVerify(token,
   jwks, { issuer, audience })`). The cookie payload is the Cognito ID token
   itself; the rest of the `verifySession()` contract (returns `{sub, name,
   iat, exp}` or `null`) is preserved.
3. Decide how the API client passes the token to the backend (see
   [21-authentication-stub.md §9.3](21-authentication-stub.md#93-backend-jwt-propagation)).
   Default is Bearer header read from `/api/auth/token`. Update
   `apps/web/lib/api.ts` once.
4. Optional: add `/register` (mirror of `/login`) calling Cognito `SignUp` +
   `ConfirmSignUp`. Until that lands, pre-create the customer in the Cognito
   console.

Cookie name, middleware matcher, top-nav account chip, login form: all stay
the same.

---

## 5. Frontend deploy (Amplify)

- Connect the GitHub repo, app root `apps/web`, build spec `amplify.yml`.
- Env from Doppler: `NEXT_PUBLIC_API_URL`, `COGNITO_REGION`,
  `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `AUTH_SECRET` (still used as
  the cookie HMAC backup until full ID-token cookies land).
- Attach the custom domain via ACM; force HTTPS.
- Manual smoke: visit the URL, sign in with the test Cognito user, upload a
  demo voyage end to end.

---

## 6. First customer onboarding

- Create the customer's user in the Cognito console (admin-create, force
  password change on first login).
- Email them the live URL and the temp password.
- Optionally seed their account with the Rotterdam demo voyage so they have
  something to look at before they upload their own.
- Walk a real voyage through the live pipeline together on the first call.

---

## 7. Must-be-done-before-money (hardening)

These are not optional once a customer is paying:

- Rate limit `POST /api/auth/login` and `POST /voyages` (App Runner / API
  Gateway layer, or in-process slowapi).
- Upload size limit (FastAPI middleware: 25 MB max per file).
- Content-type allowlist (`application/pdf` only).
- Pipeline timeout audit: every `await` has a deadline, every retry has a cap.
- DB backup policy: automated daily snapshot, 30 day retention.
- Sentry SDK in both apps with release tagging.
- CloudWatch 5xx alarm to ops email.
- Strip `print()` / `console.log` left over from dev.

---

## 8. Nice-to-have on day one (customer-driven)

- SES email send: `POST /voyages/{id}/letter/email` so the user can mail a
  filed claim to a charterer directly.
- Excel export: `GET /voyages/{id}/laytime.xlsx` via `openpyxl`. Shipping ops
  teams still live in spreadsheets.

---

## 9. Risk register

| Risk | Mitigation |
| --- | --- |
| Cookie domain mismatch between Next.js host and FastAPI host | Default to Bearer header (token never in `document.cookie`). |
| Cognito refresh token rotation | Keep ID token only in the HttpOnly cookie; refresh via a server route. |
| RDS connection pooling under App Runner cold start | Use `NullPool` in async engine for serverless v2; verify in load test. |
| S3 presigned URL leak | Use short TTL (5 min) and per-user `sub` scoping. |
| `DEV_AUTH=1` accidentally shipped | CI assertion that `DEV_AUTH=0` in `prod` Doppler config. |
| `AUTH_SECRET` fallback warning silently ignored in prod | Same CI assertion. |

---

## 10. Ranked subphase order

Ordered by what we need NOW versus what waits for a paying customer. Items in
each tier can be parallelised; tiers are sequential.

### Tier 0 — Pre-customer demo (this week)

> Workflow: all Tier 0 work ships on the `docs/first-customer-checklist`
> branch as a single rolling PR. Per-subphase branches are a Tier 2 (CI/CD)
> concern; until then we move faster on one branch.

1. **Vercel frontend deploy.** Hobby tier, connect `apps/web`, point
   `NEXT_PUBLIC_API_URL` at the App Runner URL. Half a day.
2. **P3 — App Runner backend deploy.** Build from the existing `Dockerfile`
   and `apprunner.yaml`. Env vars set in App Runner directly. `DEV_AUTH=1`,
   admin/admin auth stays on. Half a day.
3. **P9 (minimum slice) — basic upload limits.** Cap upload size, restrict to
   `application/pdf`. The full hardening waits for Tier 2. Half a day.

P6 (Sentry, minimum slice) is deferred out of Tier 0. The demo does not need
external error reporting; the local laptop demo remains the primary surface
and CloudWatch logs are enough triage for the public URL until a paying
customer arrives. P6 minimum + full now live in Tier 2 together.

### Tier 1 — Right before / on first customer

5. **P1 — Provision Cognito.** Pool + app client + JWKS. Half a day.
6. **P1 — Provision RDS Aurora Serverless v2.** Cluster + DB. Half a day,
   plus a couple of hours waiting for AWS.
7. **P1 — Provision S3.** Bucket + IAM role for App Runner. Half a day.
8. **P2 — Doppler.** Project + integrations for App Runner, Vercel (or
   Amplify), GitHub Actions. Move every secret. Half a day.
9. **Frontend auth swap.** Replace `credentials.ts` + `session.ts` with the
   Cognito + JWKS variants per Section 4. Half a day of code + review.
10. **Database migration on RDS.** `doppler run -- alembic upgrade head` once.
    Five minutes.
11. **Flip `DEV_AUTH=0`** on App Runner. Five minutes.
12. **Customer onboarding.** Admin-create the customer in Cognito, walk them
    through their first real voyage. One founder call.

### Tier 2 — Must ship before any billing

13. **P9 (full) — hardening.** Rate limits on login + voyages, pipeline
    timeout audit, error taxonomy, DB backup policy. One day.
14. **P5 — CI/CD.** GitHub Actions for lint + pytest + tsc on PR, deploy on
    merge. Half a day.
15. **P6 — observability.** Sentry on API + web (smallest install: `sentry-sdk[fastapi]`
    and `@sentry/nextjs`, no-op when the DSN is unset) plus CloudWatch 5xx
    alarm to ops email, structured logging, strip stray
    `print`/`console.log`. Half a day; combines what was previously split
    into P6 minimum (Tier 0) and P6 full (Tier 2).

### Tier 3 — First-customer-driven

16. **P4 — Amplify migration (optional).** Only if AWS-native frontend is a
    real requirement; Vercel is a fine permanent home otherwise. Half a day.
17. **P7 — SES email send.** Only if the customer wants to mail filed claims
    from the app. Half a day plus SES domain verification.
18. **P8 — Excel export.** Only if the customer asks for spreadsheets. Half
    a day.

### End-to-end timing

```
Tier 0 (demo live)              ≈ 1.5 days
Tier 1 (first customer ready)   ≈ 3 days
Tier 2 (safe to bill)           ≈ 2 days
Tier 3 (per customer ask)       ≈ 1-2 days each
```

The Tier 1 auth-swap PR can be drafted against the dev Cognito pool before the
prod pool exists, then re-pointed via env at cutover. That keeps it off the
critical path.
