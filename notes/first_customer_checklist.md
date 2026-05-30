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
| Domain (e.g. `papership.ai`) | Custom domain on Amplify + SES sender | Panos |
| Doppler workspace | Single source of truth for secrets | Roman (via GitHub Education) |
| GitHub admin on `retryoos/portside` | Service tokens, branch protections | Roman |
| Sentry org (free tier OK) | API + web error reporting | Panos |
| ANTHROPIC_API_KEY for prod | Already in use locally; cycle for prod | Panos |

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

## 10. Order of operations summary

```
Cognito + RDS + S3      (Panos, 1 day)
Doppler                 (Roman C0 + Panos P2, half a day)
alembic upgrade head    (5 minutes)
App Runner deploy       (Panos P3, half a day)
Frontend auth swap      (Roman, half a day of code + review)
Amplify deploy          (Panos P4, half a day)
Customer onboarding     (founder call, 1 hour)
CI/CD                   (Panos P5, half a day, can land after first customer)
Observability           (Panos P6, half a day, MUST be before billing)
Hardening               (Panos P9, 1 day, MUST be before billing)
SES + Excel             (Panos P7/P8, 1 day, only if customer asks)
```

End-to-end minimum: about 4 working days if Cognito + RDS provision in
parallel with the auth-swap code. The auth-swap PR can be drafted and
reviewed against the dev Cognito pool before the prod pool exists, then
re-pointed via env at cutover.
