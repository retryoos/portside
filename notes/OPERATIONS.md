# Laytimely — Operations (run + deploy)

> **Bucket 3 of 3. This is the single source of truth for running the app
> locally, the off-AWS demo deploy, and the AWS migration on first paying
> customer.** What exists lives in [SYSTEM.md](SYSTEM.md); what is planned lives
> in [ROADMAP.md](ROADMAP.md). See [README.md](README.md) for the scoping rule.
>
> Last consolidated: 2026-05-31.

---

## 1. Run it locally (the primary surface)

Prereqs: `uv` (Python), Node.js, and `ANTHROPIC_API_KEY` in `apps/api/.env`
(a repo-root `.env` also works).

```
# Terminal 1: backend
cd apps/api && uv sync && ./dev.sh          # http://localhost:8000

# Terminal 2: frontend
cd apps/web && npm install && npm run dev    # http://localhost:3000
```

Open `http://localhost:3000/cases`, click **Try the demo voyage** (offline
fixture, no backend), or **New voyage claim** -> Owner -> drop the three PDFs
from `synthetic-data/scenarios/rotterdam-weather-dispute/` and watch the
pipeline reach EUR 84,375.00.

Backend-only smoke:
```
D=synthetic-data/scenarios/rotterdam-weather-dispute
VID=$(curl -s -F cp=@$D/cp.pdf -F nor=@$D/nor.pdf -F sof=@$D/sof.pdf -F perspective=owner localhost:8000/voyages | python3 -c "import sys,json;print(json.load(sys.stdin)['voyage_id'])")
sleep 35
curl -s localhost:8000/voyages/$VID | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['stage'], d['laytime']['demurrage_due_eur'])"
# -> done 84375.0
```

---

## 2. Demo deploy — fully off AWS (current plan)

**Decision (2026-05-31): the pre-customer demo stays 100% off AWS.** AWS credits
only arrive with the first paying customer, so until then we subsidise with free
tiers and student-pack perks. Nothing must be on AWS for the demo. (The
`apps/api/Dockerfile` + `apprunner.yaml` and `apps/web/amplify.yml` remain in the
repo and are reused for the AWS migration in §4; they are not used for the demo.)

| Concern | Demo host (now) | Free via |
| --- | --- | --- |
| Frontend | **Vercel Hobby** | free tier |
| Backend (FastAPI container) | **Heroku** (container deploy of the existing `Dockerfile`) | $13/mo student credit |
| Database + auth | **Neon Postgres** + the in-app JWT stub (`DEV_AUTH`, admin/admin) | Neon free tier |
| File storage | **Cloudflare R2** (S3-compatible, via `boto3`) | R2 free tier (no egress fees) |
| Secrets | **Doppler** | student-pack Team plan |
| DNS / SSL | **Cloudflare** | free tier |

### Guiding rule for cheap migration

Lock-in lives in proprietary APIs, not infrastructure. Keep every dependency on
a standard interface (Postgres wire protocol, the S3 API via `boto3`, OCI/Docker
containers, JWT) so the AWS migration in §4 is a config change, not a rewrite.
The code already supports this: `DATABASE_URL`, `S3_BUCKET`/`S3_*`, and the
Cognito env vars are all that switch the backend between demo and prod.

> One decision to make now so auth migration is painless: demo user credentials
> are throwaway (we recreate accounts on Cognito later), and the user id is a
> UUID string, so swapping the local users table for Cognito `sub` later changes
> nothing structurally.

### 2.1 Order of operations

1. **Backend (Heroku):** containerise via the existing `apps/api/Dockerfile`
   (add a `heroku.yml` so Heroku builds the container). Set env from Doppler
   (see §3). Get the public URL; confirm `/healthz` returns `{"status":"ok"}`.
2. **Database (Neon):** create a project, set `DATABASE_URL` (asyncpg form) on
   Heroku, run `alembic upgrade head` once.
3. **File storage (R2):** create a bucket + an R2 API token; set
   `S3_ENDPOINT_URL` (the R2 endpoint), `S3_BUCKET`, `S3_ACCESS_KEY_ID`,
   `S3_SECRET_ACCESS_KEY`. Do not use any Cloudflare-specific SDK; `boto3`
   against the R2 endpoint means S3 later is a one-variable swap.
4. **Frontend (Vercel):** see §2.2.
5. **Custom domain:** see §2.3.

### 2.2 Vercel deploy

The CLI flow (equivalent to doing it in the dashboard — pick either):

```
cd apps/web
vercel link --yes                                 # scope + name the project
# NEXT_PUBLIC_API_URL is baked at BUILD time, so set it BEFORE the prod build:
printf "%s" "https://<heroku-app>.herokuapp.com" | vercel env add NEXT_PUBLIC_API_URL production
printf "%s" "$(openssl rand -hex 32)"             | vercel env add AUTH_SECRET production
vercel --prod                                     # returns https://<project>.vercel.app
```

Then add the Vercel URL to the backend `CORS_ORIGINS` (Heroku config) and redeploy,
and smoke an end-to-end upload from the Vercel URL (Network tab: `POST /voyages`
returns 201, no CORS error).

> The dashboard route is identical: Project -> Settings -> Environment Variables
> for the two vars, then a deploy. Only hard rule: `NEXT_PUBLIC_API_URL` must be
> set before the production build.

### 2.3 Custom domain (`laytimely.com`) on Cloudflare

The domain was bought from Namecheap and its nameservers already point at
Cloudflare, so **Cloudflare is authoritative for DNS now.** The 60-day registrar
transfer lock only affects billing/registration, not DNS — create records today.

1. Vercel -> Project -> Settings -> Domains: add `laytimely.com` and
   `www.laytimely.com`. Vercel prints the exact records.
2. In Cloudflare DNS, create them (typically apex `laytimely.com` -> A record to
   Vercel's IP, e.g. `76.76.21.21`; `www` -> CNAME `cname.vercel-dns.com` — use
   whatever the Vercel dashboard shows).
3. **Set both records to DNS only (grey cloud), not Proxied (orange cloud).**
   Vercel issues its own SSL cert and handles the apex/www redirect; leaving
   Cloudflare's proxy on causes cert-verification failures and redirect loops.
4. In Vercel, set one domain as **Primary** (recommend apex `laytimely.com`);
   Vercel auto-redirects `www` -> apex. Do not hand-build the redirect.
5. Add `https://laytimely.com` (and `https://www.laytimely.com`) to backend
   `CORS_ORIGINS`.

---

## 3. The environment-variable contract

Everything external is reached through env vars (see [SYSTEM.md §7](SYSTEM.md)).
Hardcode nothing; this contract is what makes §4 a config change.

```
# transport / model
ANTHROPIC_API_KEY        ANTHROPIC_MODEL_PRIMARY=claude-sonnet-4-6   ANTHROPIC_MODEL_ESCAPE=claude-opus-4-7
REQUEST_TIMEOUT_S=30     CORS_ORIGINS=<the live frontend origins>

# database + auth (tied now, untied in §4)
DATABASE_URL             # Neon now -> Aurora later
DEV_AUTH=1               # stub now; flip to 0 once Cognito exists
AUTH_SECRET              # web cookie HMAC (random 32+ chars, even in demo)
COGNITO_REGION / COGNITO_USER_POOL_ID / COGNITO_CLIENT_ID   # unset now; set in §4

# file storage (R2 now -> S3 later)
S3_ENDPOINT_URL          # R2 endpoint now; unset for real AWS S3 in §4
S3_BUCKET  S3_REGION  S3_ACCESS_KEY_ID  S3_SECRET_ACCESS_KEY  (S3_PREFIX)

# feature flags (default off; flip per readiness) — see SYSTEM.md §7
EMAIL_SEND_LIVE  EMAIL_IN_SHARED_SECRET  INBOX_DOMAIN  WORKSPACES_UI
RESEARCH_LIVE  LEGAL_EUR_LEX_LIVE  LEGAL_BAILII_LIVE
SES_SENDER  INVITATION_BASE_URL
```

Doppler holds all of it (project `laytimely`, configs `dev` / `staging` /
`prod`); local laptops use `doppler run` rather than `.env`. Keep
`.env.example` committed as documentation only.

---

## 4. First paying customer — the AWS migration

Triggered by the first paying customer (AWS credits land then). Done in parallel
with business registration. Nothing in the product code rewrites; this is
provisioning + config + one auth-swap code change. Provisioning steps are
independent except: RDS must exist before `alembic upgrade head`, and Doppler
before secrets leave laptops.

**Target topology:** Vercel (or Amplify) frontend -> ECS Fargate (or App Runner)
backend -> Aurora Serverless v2 Postgres + S3 + Cognito, secrets in Doppler.

### 4a. Cognito (auth)
User pool with email alias, password policy (min 12, mixed case, digit, symbol),
optional MFA. App client (with secret if the Next.js server brokers
`InitiateAuth`). Set `COGNITO_REGION/USER_POOL_ID/CLIENT_ID` and `DEV_AUTH=0` —
the backend (`auth.py`) then verifies real JWTs with **no code change**
(issuer/JWKS derived in `settings.py`). The one code change is the frontend auth
swap: `lib/auth/credentials.ts` calls Cognito `InitiateAuth` and returns the
`IdToken`; `lib/auth/session.ts` verifies it via `jose.createRemoteJWKSet`.
Cookie name, middleware, and the rest of the session contract stay. Because demo
credentials are throwaway, **no password migration** — recreate accounts in
Cognito (admin-create, force change on first login).

### 4b. RDS Aurora Serverless v2 (database)
Single cluster, `db.serverless` writer, min 0.5 / max 4 ACU. Two-AZ subnet
group; security group for the backend's VPC connector. Create an app user and a
`laytimely` database. Compose `DATABASE_URL` as
`postgresql+asyncpg://user:pass@endpoint:5432/laytimely`. Migrate the demo data
with `pg_dump | psql` from Neon, then `doppler run --config prod -- alembic -c
apps/api/alembic.ini upgrade head`. Use `NullPool` in the async engine for
serverless cold starts.

### 4c. S3 (file storage)
Bucket `laytimely-voyages-prod-<region>`, block public access, SSE-S3 (or
SSE-KMS if compliance demands). Lifecycle to STANDARD_IA after 30 days, no
auto-delete. IAM role for the backend with `s3:PutObject`/`s3:GetObject` scoped
to `voyages/*`. Copy objects from R2, then **unset `S3_ENDPOINT_URL`** so
`boto3` hits AWS — that one removal is the whole storage migration.

### 4d. Backend on AWS
Push the same Docker image to ECR; run on ECS Fargate (or App Runner via the
existing `apprunner.yaml`). Env from Doppler: every key in §3 plus `DEV_AUTH=0`
and `CORS_ORIGINS=https://laytimely.com`. Health check `/healthz`.

### 4e. Cutover
Repoint the `api` DNS record at the AWS backend; flip `DEV_AUTH=0`; verify a
call without a token returns 401 and with a real Cognito token returns 200
scoped to that user's `sub`.

---

## 5. Hardening before any billing (Tier 2)

Already landed in code: rate limit on `POST /voyages`, upload size + content-type
limits, security headers on both tiers, generic-error hardening, `AUTH_SECRET`
fails closed in production.

Still required before charging money:
- Rate limit `POST /api/auth/login` (lives in the Next.js app).
- Pipeline timeout/retry audit (every `await` has a deadline, every retry a cap).
- DB backup policy: automated daily snapshot, 30-day retention.
- Sentry on both apps with release tagging; CloudWatch 5xx + p95 alarms to ops.
- CI assertion that `DEV_AUTH=0` in the `prod` Doppler config.
- Strip stray `print` / `console.log`.
- CI/CD: GitHub Actions for lint + pytest + tsc on PR, deploy on merge.
- A Playwright golden-path E2E (upload -> done -> letter).

---

## 6. If a deploy stalls

The local laptop demo is the canonical surface; never block a demo on a deploy.
An investor-grade run works locally (`./dev.sh` + `npm run dev`), and the Vercel
deploy stays useful against a placeholder `NEXT_PUBLIC_API_URL` because "Try the
demo voyage" renders the offline fixture end to end with no backend.

---

## 7. Cost guardrail

- **Demo:** Heroku (student credit), Neon (free), R2 (free, no egress), Vercel
  Hobby (free), Cloudflare (free) -> effectively $0/mo.
- **Anthropic is the real cost:** ~EUR 0.05-0.10 per voyage (Sonnet 4.6 +
  prompt caching). Do not advertise a public URL to anything that could loop.
- **Post-migration AWS:** Aurora v2 is not free; that is what the first-customer
  AWS credits cover.
