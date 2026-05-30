# Tier 0 deploy plan (Panos's track, taking over)

> Action plan for the four Tier 0 subphases that bring the demo live on a
> public URL. Source of truth is
> [first_customer_checklist.md §10 Tier 0](first_customer_checklist.md#tier-0--pre-customer-demo-this-week);
> subphase content originates in
> [19-production-reasoning-panos.md](19-production-reasoning-panos.md). The
> authentication stub is preserved per
> [21-authentication-stub.md](21-authentication-stub.md). This plan lists, for
> each subphase: the branch, the files I will touch, the env vars, the human
> blockers, the CLI I will run, and the acceptance evidence I will capture.
>
> Tier 1 (Cognito, RDS, S3, Doppler), Tier 2 (full hardening, CI/CD, full
> observability), and Tier 3 (Amplify, SES, Excel) are out of scope for this
> plan.

---

## 1. Scope and non-goals

In scope, in shipping order:

1. **P0**, Vercel frontend deploy of `apps/web` on Hobby tier.
2. **P3**, AWS App Runner backend deploy from `apps/api/Dockerfile` via
   `apps/api/apprunner.yaml`.
3. **P9 minimum**, upload size cap (25 MB per file) and content-type allowlist
   (`application/pdf` only) on `POST /voyages`.
4. **P6 minimum**, smallest viable Sentry install on both apps, no-op when the
   DSN env var is absent.

Out of scope, do not touch in these four PRs:

- `apps/api/portside_api/schemas.py` and `apps/web/lib/types.ts` are FROZEN.
  None of P0, P3, P9 min, or P6 min require changes there. If a follow-up
  surfaces a real need, I announce on the PR and mirror both sides; until then
  the contracts stay still.
- `apps/api/portside_api/agents/calculator.py` and
  `apps/api/tests/test_calculator.py`. The owner gate at `84,375.0 EUR` and
  the charterer gate at `76,875.0 EUR` must stay green. Never touched.
- `apps/api/portside_api/auth.py` and the `DEV_AUTH=1` path. `admin / admin`
  stays the login throughout Tier 0; Cognito is Tier 1.
- Doppler, RDS, S3, Cognito, SES, custom domains. All Tier 1 or later.

Hard rules I will not violate:

- No em dashes anywhere in code, prose, or commit messages. Use commas,
  periods, colons. A previous cleanup commit removed them from the codebase;
  do not reintroduce.
- One PR per subphase. Small, disjoint file set, self-verifying.
- Money is never owned by the model. The calculator and its test are
  off-limits.
- Match the project commit-message style: subject line, blank line, body,
  `Co-Authored-By: Claude <noreply@anthropic.com>` trailer.

---

## 2. Branching and PR layout

| # | Subphase | Branch | Base | Files (approx.) | Tests |
| --- | --- | --- | --- | --- | --- |
| 0 | This plan | `docs/first-customer-checklist` (current) | `main` | `notes/22-tier-0-deploy-plan.md` only | n/a |
| 1 | P0 Vercel | `feat/p0-vercel-frontend` | `main` | `apps/web/.env.example`, optional `apps/web/README.md` blurb, optional repo-root `.vercelignore` | none, deploy-time verification |
| 2 | P3 App Runner | `feat/p3-app-runner-deploy` | `main` | `apps/api/apprunner.yaml`, `apps/api/.env.example`, `notes/16-aws-deploy.md` (Tier 0 click-through update) | existing suite stays green |
| 3 | P9 minimum | `feat/p9-min-upload-limits` | `main` | `apps/api/portside_api/limits.py` (new), `apps/api/portside_api/main.py` (the `create_voyage` handler only), `apps/api/tests/test_upload_limits.py` (new) | new tests for 413 and 415, plus the existing suite still green |
| 4 | P6 minimum | `feat/p6-min-sentry` | `main` | `apps/api/pyproject.toml`, `apps/api/uv.lock`, `apps/api/portside_api/sentry.py` (new), `apps/api/portside_api/main.py` (one-line import), `apps/api/apprunner.yaml`, `apps/api/.env.example`, `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/instrumentation.ts` (new), `apps/web/sentry.client.config.ts` (new), `apps/web/sentry.server.config.ts` (new), `apps/web/sentry.edge.config.ts` (new), `apps/web/.env.example` | new no-op tests asserting `Sentry.init` is safe with an empty DSN |

Order of merge: the current docs PR first, then P0, then P3, then P9 minimum,
then P6 minimum. The P0 and P3 PRs are independent at the code level (P0 is
config-only on the Vercel side, P3 is config-only on the App Runner side);
the deploys themselves interleave (see §3.3).

The branches off `main` are short-lived. Each one is rebased on `main` right
before merge so its diff stays small and reviewable.

---

## 3. Subphase plans

### 3.1 P0, Vercel frontend deploy

**Goal.** A public `https://*.vercel.app` URL serving `apps/web`, pointing at
the App Runner backend, with `admin / admin` working end to end.

**Why config-only.** `apps/web/lib/api.ts` already reads `NEXT_PUBLIC_API_URL`
with a `http://localhost:8000` fallback. `apps/web/middleware.ts` plus the
auth stub described in
[21-authentication-stub.md](21-authentication-stub.md) already handle the
session cookie. P0 only needs the frontend hosted with two env vars set.

**Files I will touch in the PR.**

- `apps/web/.env.example`, add the two env vars used by the deploy:
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - `AUTH_SECRET=local-dev-secret-please-do-not-deploy-this`
- Optional: `apps/web/README.md` (one short section, "Deploying to Vercel
  Hobby", with the env vars and the `vercel link` command).
- Optional: a top-level `.vercelignore` to exclude `apps/api/`,
  `synthetic-data/`, `notes/`, and the local `apps/api/_objects/` directory
  from upload context. Reduces deploy size; not strictly required because
  Vercel only builds the project root we point it at.

No code changes in `apps/web/app/`, `apps/web/lib/`, or `apps/web/components/`.

**Env vars set in Vercel (project settings, all three environments).**

| Name | Production | Preview | Development |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | App Runner URL from P3 | App Runner URL | leave unset (uses localhost fallback) |
| `AUTH_SECRET` | `openssl rand -hex 32` value | same as production or a separate value | leave unset (uses local dev fallback) |

`NEXT_PUBLIC_API_URL` is baked at build time. Any rotation of the App Runner
URL requires a redeploy on Vercel; not a concern for Tier 0 because the App
Runner URL is stable for the life of the service.

**Human blockers (no CLI substitute).**

1. Create or confirm the Vercel account on the Hobby plan.
2. Run `vercel login` locally and confirm via email. Paste back the email
   address used so I can sanity-check the project ownership.
3. Confirm we are connecting Vercel to the GitHub repo `retryoos/portside`,
   not a fork, so the deploy auto-rebuilds on push.

**What I will do via CLI after the human gates clear.**

```
npm install -g vercel
cd apps/web
vercel link --yes --project papership-web
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_API_URL preview
vercel env add AUTH_SECRET production
vercel env add AUTH_SECRET preview
vercel --prod
```

Alternative: connect via the Vercel GitHub integration in the dashboard and
use the CLI only for env vars. Both work. CLI-led is faster for the demo and
gives me a stable record of the commands.

**Order dependency on P3.** `NEXT_PUBLIC_API_URL` must be set to the App
Runner URL before the first production build. Two options:

- Land P3 first, capture the App Runner URL, then run the P0 deploy. Cleanest.
- Or do a placeholder Vercel deploy (using a dummy URL) just to confirm the
  build passes, then swap `NEXT_PUBLIC_API_URL` and redeploy once P3 is live.

I will follow the user's stated order (P0 PR opens first), then perform the
actual Vercel deploy after the App Runner URL exists. The PR is independent
of the deploy step.

**Acceptance.**

- The public Vercel URL renders `/login`. The redirect from `/` to `/login`
  works (existing middleware).
- POST `/api/auth/login` with `{ "username": "admin", "password": "admin" }`
  returns `200` and sets the `portside_session` cookie.
- Visiting `/cases` after login shows the dashboard, and either the offline
  "Try the demo voyage" path renders, or a real upload reaches the live
  App Runner backend and progresses through `extracting` to `done` with
  `demurrage_due_eur = 84375.0`.

**Evidence I will capture in the PR description and the follow-up message.**

- The Vercel project URL.
- A `curl -i $URL/api/auth/me` showing `401 { "user": null }` when signed
  out.
- A screenshot or copy of the dashboard reaching `/cases` after login.
- A `voyage_id` from a live upload that reaches `stage=done` with the
  correct quantum.

**Risks.**

- The Vercel build can fail on a stale or mismatched lockfile. We use
  `package-lock.json` committed; the build spec runs `npm ci`. If the build
  is red, I run `npm install` locally on a fresh checkout to reproduce, and
  commit any lockfile drift in a follow-up commit on the same branch.
- `NEXT_PUBLIC_*` baked at build time means a CORS mismatch after the fact
  requires a redeploy. Mitigated by capturing the App Runner URL once and
  not rotating it during Tier 0.

---

### 3.2 P3, AWS App Runner backend deploy

**Goal.** A public App Runner service URL serving the FastAPI app, with
`DEV_AUTH=1`, `admin / admin` auth preserved, the live `ANTHROPIC_API_KEY`
set, and CORS locked to the Vercel URL once known.

**Files I will touch in the PR.**

- `apps/api/apprunner.yaml`:
  - Declare `DEV_AUTH` in the `env` block with the value `"1"`. The runtime
    default in `portside_api/settings.py` already falls back to dev auth when
    no Cognito pool is set, but an explicit `DEV_AUTH=1` is the safer
    contract: it leaves no doubt for a reader of the manifest.
  - Update the `CORS_ORIGINS` placeholder comment to reflect the Vercel URL
    rather than the Amplify URL.
  - Leave the `set-via-console` placeholder for `ANTHROPIC_API_KEY` in place.
- `apps/api/.env.example`:
  - Add a documented stanza of the App Runner env names so the next operator
    sees the full list. The file already exists, I will add or correct
    entries only.
- `notes/16-aws-deploy.md`:
  - Add or update a small Tier 0 section: explicit App Runner click-through,
    `DEV_AUTH=1`, `CORS_ORIGINS = <Vercel URL>`, source-deploy via
    `apprunner.yaml`. The existing doc was written for the hackathon-era
    Amplify topology and needs to track the Vercel-first reality.

No changes to `apps/api/portside_api/*.py` and no migration changes.

**Env vars set on the App Runner service (console, secrets where noted).**

| Name | Value | Notes |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Real key (secret) | Bind via console secret; never committed |
| `DEV_AUTH` | `1` | Preserves `admin / admin` |
| `CORS_ORIGINS` | `https://<vercel-prod-url>` | Update once P0 yields the URL; lock down to the prod URL plus the previews if needed |
| `ANTHROPIC_MODEL_PRIMARY` | `claude-sonnet-4-6` | Already defaulted in `apprunner.yaml` |
| `ANTHROPIC_MODEL_ESCAPE` | `claude-opus-4-7` | Same |
| `REQUEST_TIMEOUT_S` | `30` | Same |

**Human blockers.**

1. AWS account with billing set up, IAM admin user or an SSO role with
   App Runner, ECR (if I push images), and CloudWatch permissions.
2. `aws configure sso` (or `aws configure`) completed locally so my shell
   can talk to AWS.
3. Paste back the output of `aws sts get-caller-identity` so I can confirm
   which account and which role I am operating under.
4. The first App Runner service creation click-through in the console. The
   GitHub source connection step requires an OAuth handshake that only the
   console can complete. After the connection exists I can drive subsequent
   redeploys from the CLI.
5. The real `ANTHROPIC_API_KEY` value for production. Paste it in a private
   channel; I will type it into the App Runner console (and never log it).

**What I will do via CLI after the human gates clear.**

- `aws sts get-caller-identity`, sanity check.
- `aws apprunner list-connections`, confirm the GitHub connection is in
  `AVAILABLE`.
- If we go ECR-mode instead of source-deploy:
  - `docker build -t portside-api apps/api`
  - `aws ecr create-repository --repository-name portside-api`
  - `aws ecr get-login-password ... | docker login ...`
  - `docker tag` and `docker push`
  - `aws apprunner create-service ...` with an `ImageRepository` source.
- If we go source-deploy (preferred for Tier 0 because `apprunner.yaml`
  carries the runtime config and the GitHub connection already exists):
  - `aws apprunner create-service --service-name portside-api ...
    --source-configuration CodeRepository=...` (or click-through). Either way
    the YAML drives the build.
- After service is `RUNNING`:
  - `curl https://<id>.<region>.awsapprunner.com/healthz` should print
    `{"status":"ok"}`.
- Update `CORS_ORIGINS` once the Vercel URL exists (a single env-var edit on
  the service triggers a fast redeploy).

**Acceptance.**

- `GET /healthz` returns `{"status":"ok"}` against the App Runner URL.
- From the Vercel frontend, a live upload of the three demo PDFs reaches
  `stage=done` with `demurrage_due_eur = 84375.0`.
- `cd apps/api && uv run pytest -q` still green on the branch before merge.

**Evidence I will capture.**

- The App Runner service URL.
- Curl output for `/healthz`.
- A `voyage_id` from a live end-to-end run, with the final state showing
  `stage=done` and the quantum.
- Cloudwatch link to the build log (optional).

**Risks.**

- App Runner ARM vs x86 base image mismatch. Our `Dockerfile` is
  `python:3.12-slim`; App Runner builds on its own runner so we are fine.
- First build budget is around fifteen minutes per
  [notes/16-aws-deploy.md](16-aws-deploy.md). Plan for it.
- Cold-start latency on min-instances zero (App Runner default) is around
  five seconds. Acceptable for a demo. If we cannot tolerate it we bump
  min-instances to one (extra cost) before the demo.
- `DEV_AUTH=1` is a known footgun in production. Tier 1 flips it to `0`
  along with Cognito. Until then it stays on and we never advertise the
  URL beyond demo viewers.

---

### 3.3 Cross-deploy chicken-and-egg

P0 wants `NEXT_PUBLIC_API_URL` (a P3 output). P3 wants `CORS_ORIGINS` (a P0
output). Resolution:

1. P3 PR opens with the YAML changes; the service is created with
   `CORS_ORIGINS = http://localhost:3000` as a placeholder so the build can
   come up. Note the App Runner URL.
2. P0 PR opens with the Vercel config changes; deploy the project with
   `NEXT_PUBLIC_API_URL = <App Runner URL>`. Note the Vercel URL.
3. Back in App Runner, edit `CORS_ORIGINS` to
   `https://<vercel-url>` (and add the preview URL if we want previews to
   talk to the same backend). Redeploys in around two minutes.
4. Smoke the loop from the Vercel URL: dashboard renders, login works,
   upload reaches `done`.

This is captured in the P3 PR description so the reviewer can replay the
sequence.

---

### 3.4 P9 minimum, upload limits

**Goal.** Reject uploads larger than 25 MB per file with HTTP 413, and
reject any file whose content-type is not `application/pdf` with HTTP 415,
on `POST /voyages`. The full hardening (rate limits, pipeline timeout audit,
error taxonomy, DB backup policy) is Tier 2 and not in this PR.

**Files I will touch in the PR.**

- New: `apps/api/portside_api/limits.py`. Two constants and one helper.
  ```
  MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB per file
  ALLOWED_CONTENT_TYPES = frozenset({"application/pdf"})
  ```
  Plus an `async def validate_and_read(upload: UploadFile) -> bytes` that:
  - Raises `HTTPException(415, ...)` if `upload.content_type` is not in the
    allowlist (or is missing).
  - Reads up to `MAX_UPLOAD_BYTES + 1` bytes; if the read returned more than
    `MAX_UPLOAD_BYTES`, raises `HTTPException(413, ...)`.
  - Returns the bytes on success. Single source of truth; keeps the route
    handler small.
- `apps/api/portside_api/main.py`, only the `create_voyage` handler:
  - Replace the three inline `await cp.read()` calls with
    `await validate_and_read(cp)` etc.
  - No other lines touched. Imports the new module.
- New: `apps/api/tests/test_upload_limits.py`. Three cases:
  1. A 30 MB PDF returns `413` and never touches the store.
  2. A `.docx` upload (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
     returns `415` and never touches the store.
  3. A normal small PDF still creates a voyage (regression test that the
     happy path is not broken).
- No changes to `apps/api/portside_api/schemas.py`, `apps/web/lib/types.ts`,
  the calculator, the gate test, or `auth.py`.

**Test design notes.**

- Use the existing `TestClient`-based tests in `test_main_async.py` as the
  template. Build a tiny in-memory PDF byte string for the happy path; build
  a 26 MB byte string padded with zeros for the 413 case (this never reaches
  the agents because the limit fires first).
- Stay under the `pytest -q` runtime budget of the rest of the suite. A
  30 MB byte string in memory is fine on CI; the test does not write to
  disk.

**Acceptance.**

- `cd apps/api && uv run pytest -q` is green, including the 84,375 gate
  test (which I never touch).
- Manual smoke against the live App Runner URL once P3 is up:
  - A 30 MB upload returns `413`.
  - A `.docx` upload returns `415`.

**Evidence I will capture.**

- The pytest output excerpt with the new tests passing and the gate test
  passing.
- Two curl traces against the live API, one 413 and one 415.

**Risks.**

- FastAPI buffers `UploadFile` to a temporary spool. Reading past 25 MB
  before deciding is wasted I/O but not a correctness issue at Tier 0 traffic
  levels. Full hardening adds an upstream content-length guard.
- The 415 case relies on the client sending a content-type. Browsers do; a
  hand-crafted `curl` without a content-type header would surface as
  `application/octet-stream` or empty, both of which fail the allowlist.
  This is the intended behaviour.

---

### 3.5 P6 minimum, Sentry on both apps

**Goal.** Install Sentry on the API and the web with the smallest viable
config. Reading `SENTRY_DSN_API` and `SENTRY_DSN_WEB` from env. When the
DSN is missing the SDK is a no-op so local dev is unaffected.

**API side, files in the PR.**

- `apps/api/pyproject.toml`: add `sentry-sdk[fastapi]` to `dependencies`.
- `apps/api/uv.lock`: regenerated via `uv lock`.
- New: `apps/api/portside_api/sentry.py`. Single function:
  ```
  def init_sentry() -> None:
      dsn = os.environ.get("SENTRY_DSN_API")
      if not dsn:
          return
      sentry_sdk.init(
          dsn=dsn,
          traces_sample_rate=0.0,  # no perf in Tier 0
          send_default_pii=False,
          integrations=[FastApiIntegration()],
      )
  ```
- `apps/api/portside_api/main.py`: one new import and one new call before
  `app = FastAPI(...)`:
  ```
  from .sentry import init_sentry

  init_sentry()
  ```
- `apps/api/apprunner.yaml`: declare `SENTRY_DSN_API` in the `env` block,
  value `"set-via-console"`.
- `apps/api/.env.example`: add `SENTRY_DSN_API=` (empty by default so local
  dev stays a no-op).

**Web side, files in the PR.**

- `apps/web/package.json`: add `@sentry/nextjs` to `dependencies`.
- `apps/web/package-lock.json`: regenerated via `npm install`.
- New: `apps/web/instrumentation.ts`:
  ```
  export async function register() {
    if (process.env.NEXT_RUNTIME === "nodejs") {
      await import("./sentry.server.config");
    }
    if (process.env.NEXT_RUNTIME === "edge") {
      await import("./sentry.edge.config");
    }
  }
  ```
- New: `apps/web/sentry.server.config.ts`, `sentry.edge.config.ts`,
  `sentry.client.config.ts`. Each one:
  ```
  import * as Sentry from "@sentry/nextjs";
  const dsn = process.env.SENTRY_DSN_WEB;
  if (dsn) {
    Sentry.init({
      dsn,
      tracesSampleRate: 0,
      sendDefaultPii: false,
    });
  }
  ```
  When `SENTRY_DSN_WEB` is unset, `Sentry.init` is never called and the SDK
  is effectively a no-op.
- `apps/web/.env.example`: add `SENTRY_DSN_WEB=`.
- I will deliberately NOT wrap `next.config.mjs` with `withSentryConfig`.
  Source map upload, release tagging, and tunnel routes are Tier 2 (full P6)
  and not needed for the minimum slice.

**Env vars.**

| App | Env var | Set where |
| --- | --- | --- |
| API | `SENTRY_DSN_API` | App Runner console (secret) |
| Web | `SENTRY_DSN_WEB` | Vercel project env (production, preview) |

The web DSN is intentionally NOT exposed as `NEXT_PUBLIC_SENTRY_DSN_WEB`;
client-side Sentry on Next.js 15 reads the DSN at build time from the
non-public env when configured via the `sentry.client.config.ts` route, then
inlines it during the build. The user can choose to expose it as a public
env if they want a separate frontend Sentry org; the minimum slice keeps
both on a single web DSN.

**Human blockers.**

1. Create or confirm a Sentry org (free tier is enough).
2. Create two projects: `papership-api` (Python / FastAPI) and
   `papership-web` (Next.js).
3. Paste back the two DSN strings. I will type them into the App Runner and
   Vercel consoles.

**What I will do via CLI.**

- API side: `cd apps/api && uv add 'sentry-sdk[fastapi]' && uv lock`.
- Web side: `cd apps/web && npm install --save @sentry/nextjs`.
- Run the existing test suite. The new no-op test verifies an empty DSN does
  not crash and does not send to a network.
- Smoke after deploy: a one-shot script `apps/api/scripts/sentry_smoke.py`
  (and an `apps/web/scripts/sentry-smoke.ts` equivalent) that triggers a
  captured exception, run once after the DSN env vars land. The scripts are
  test artifacts, not user-facing routes. I will NOT ship a debug endpoint
  to production traffic.

**Acceptance.**

- An intentional unhandled exception in the API reaches the Sentry
  `papership-api` project within 30 seconds.
- Same for the web in `papership-web`.
- With both DSN env vars unset, `uv run pytest -q` is green and
  `npm run build` plus `npx tsc --noEmit` are green.

**Evidence I will capture.**

- Sentry issue links for both apps.
- Pytest and tsc green output.
- The smoke scripts removed if we judge them noisy, kept in `scripts/` if we
  judge them useful for future Tier 2 work.

**Risks.**

- `@sentry/nextjs` major versions sometimes shift the recommended init
  shape. I will pin to the current stable release line and document the
  version in `package.json`.
- The FastAPI integration adds a small import-time cost. With DSN unset we
  short-circuit before importing, so cold-start is unchanged.
- A misconfigured `instrumentation.ts` can break `next build`. Verified
  locally before pushing.

---

## 4. Operational order and timing

Calendar order, with the actual blocking dependencies between subphases:

```
day 1 morning
  [human]    confirm Vercel and AWS accounts, run vercel login + aws configure
  [human]    paste back: email + aws sts get-caller-identity + ANTHROPIC_API_KEY
  [me]       open PR0 (this doc), merge after review
  [me]       open PR1 (P0 Vercel config), keep open until P3 URL exists
  [me]       open PR2 (P3 App Runner config), merge
  [human]    click through App Runner service creation in console
  [me]       capture App Runner URL, set CORS_ORIGINS placeholder, smoke /healthz
day 1 afternoon
  [me]       set NEXT_PUBLIC_API_URL in Vercel, deploy production
  [me]       capture Vercel URL, update App Runner CORS_ORIGINS to the Vercel URL
  [me]       smoke an end-to-end upload through the Vercel frontend
  [me]       merge PR1 (P0 Vercel config)
day 2 morning
  [me]       open PR3 (P9 minimum upload limits), local pytest -q green
  [me]       merge PR3, App Runner redeploys, repeat the curl smokes for 413/415
day 2 afternoon
  [human]    create Sentry org + two projects, paste back the two DSNs
  [me]       open PR4 (P6 minimum Sentry), local build + pytest -q green
  [me]       set DSN env vars on App Runner and Vercel, redeploy both
  [me]       run smoke scripts, capture Sentry issue links, merge PR4
```

Total wall-clock budget is roughly two engineering days, dominated by AWS
provisioning latency and AWS console click-throughs. Anthropic API calls are
incidental.

---

## 5. Human-only blockers (single concise asks)

Below are the messages I will send the user, exactly once per blocker, and
then wait. No improvising around them.

1. P0 unblock: "I need you to run `vercel login` in your terminal and paste
   back the email you used. Confirm you are on Hobby tier. Reply when done."
2. P3 unblock: "I need you to run `aws configure sso` (or `aws configure`)
   and then paste back the output of `aws sts get-caller-identity` so I can
   see which account I am pointed at. Also paste the production
   `ANTHROPIC_API_KEY` value in our private channel."
3. P3 console step: "I need you to click through the App Runner service
   creation in the AWS console once, using `apps/api/apprunner.yaml` as the
   source config and the GitHub connection to `retryoos/portside`. Paste the
   service URL when the service is `RUNNING`."
4. P6 unblock: "I need you to create a Sentry org plus two projects
   (`papership-api`, FastAPI; `papership-web`, Next.js) and paste both DSNs."

If any one of these is missing I stop and wait. I do not invent stand-ins.

---

## 6. Acceptance summary (the four greens that ship the demo)

- A public Vercel URL renders `/cases` after `admin / admin` login.
- A public App Runner URL returns `{"status":"ok"}` on `GET /healthz`.
- An upload from the Vercel frontend reaches `stage=done` with
  `demurrage_due_eur = 84375.0`.
- A 30 MB upload returns 413, a `.docx` upload returns 415, and the
  pytest suite (including the 84,375 gate) is green.
- An intentional unhandled exception on each app surfaces in the
  corresponding Sentry project within 30 seconds.

When all five lines are green, Tier 0 is shipped. Tier 1 starts.

---

## 7. Pre-existing issues I noticed but will not fix in this plan

- `apps/api/portside_api/main.py` has two `@app.delete("/voyages/{voyage_id}")`
  registrations. The first is owner-scoped via `Depends(get_current_user)`;
  the second redefines the function without auth and calls
  `store.delete(voyage_id)` without an owner id. Starlette keeps the first
  match, so the auth path wins at runtime, but the dead second route is
  confusing and should be removed in a separate small PR (not P9 minimum,
  not P6 minimum). Filed as a follow-up.
- `apps/api/apprunner.yaml` and several other files contain em dashes
  inherited from before the previous cleanup. They are not in the Tier 0
  diff. I will not regress on this rule: every new line I write here uses
  commas, periods, and colons. A dedicated em-dash sweep is its own PR if
  the user wants it.
- `notes/17-pre-deployment.md` was written for the day-of hackathon AWS
  flex (Amplify + App Runner) and references the older topology. It is not
  wrong, just historical. Tier 0 supersedes it; I am not editing it.

---

## 8. What I report after each subphase merges

A short message, every time, with these five lines:

1. What I did (the PR link, the files touched).
2. What is live (the URL).
3. The acceptance evidence (curl trace, screenshot, or pytest excerpt).
4. What is left for the human (paste-back asks, if any).
5. The next subphase I am starting.

If I discover the checklist drifted from reality, the checklist is the bug,
and I fix it on `docs/first-customer-checklist` before continuing.
