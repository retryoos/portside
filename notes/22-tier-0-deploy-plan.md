# Tier 0 deploy plan (Panos's track, taking over)

> Action plan for the Tier 0 subphases that bring the demo live on a public
> URL. Source of truth is
> [first_customer_checklist.md §10 Tier 0](first_customer_checklist.md#tier-0--pre-customer-demo-this-week);
> subphase content originates in
> [19-production-reasoning-panos.md](19-production-reasoning-panos.md). The
> authentication stub is preserved per
> [21-authentication-stub.md](21-authentication-stub.md). This plan lists, for
> each subphase: the files touched, the env vars, the human blockers, the CLI
> to run, and the acceptance evidence to capture.
>
> Workflow update (per founder direction): all Tier 0 work ships on the
> `docs/first-customer-checklist` branch as a single rolling PR. The original
> "one branch per subphase" discipline is a Tier 2 (CI/CD) concern; until
> then we move faster on one branch.
>
> Scope update: P6 minimum (Sentry on both apps) is deferred out of Tier 0
> and folded into the full P6 in Tier 2. The demo does not need external
> error reporting; the laptop remains the primary surface and CloudWatch
> logs are enough triage for the public URL until a paying customer arrives.
>
> Remaining Tier 0 subphases: P0 (Vercel frontend deploy), P3 (App Runner
> backend deploy), P9 minimum (upload size cap + content-type allowlist).
>
> Tier 1 (Cognito, RDS, S3, Doppler), Tier 2 (full hardening, CI/CD, full
> observability including Sentry), and Tier 3 (Amplify, SES, Excel) are out
> of scope for this plan.

---

## 1. Scope and non-goals

In scope, in shipping order, all on the `docs/first-customer-checklist` branch:

1. **P0**, Vercel frontend deploy of `apps/web` on Hobby tier.
2. **P3**, AWS App Runner backend deploy from `apps/api/Dockerfile` via
   `apps/api/apprunner.yaml`.
3. **P9 minimum**, upload size cap (25 MB per file) and content-type allowlist
   (`application/pdf` only) on `POST /voyages`.

Out of scope, do not touch in this PR:

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
- Money is never owned by the model. The calculator and its test are
  off-limits.
- Match the project commit-message style: subject line, blank line, body,
  `Co-Authored-By: Claude <noreply@anthropic.com>` trailer.

---

## 2. Branch and PR layout

Single working branch: `docs/first-customer-checklist`. Single rolling PR
([#27](https://github.com/retryoos/portside/pull/27)) that absorbs every
Tier 0 commit. Founder direction: ship, do not litter the repo with
per-subphase branches at this stage.

Commits land in this logical order, each one self-contained:

| # | Subphase | Files (approx.) | Tests |
| --- | --- | --- | --- |
| 1 | Plan + checklist updates | `notes/22-tier-0-deploy-plan.md`, `notes/first_customer_checklist.md` (this commit) | n/a |
| 2 | P0 Vercel config | `apps/web/.env.example`, optional `.vercelignore` | none, deploy-time verification |
| 3 | P3 App Runner config | `apps/api/apprunner.yaml`, `apps/api/.env.example`, `notes/16-aws-deploy.md` (Tier 0 click-through update) | existing suite stays green |
| 4 | P9 minimum upload limits | `apps/api/portside_api/limits.py` (new), `apps/api/portside_api/main.py` (the `create_voyage` handler only), `apps/api/tests/test_upload_limits.py` (new) | new tests for 413 and 415, existing suite still green |

Each commit message follows the project style and explains the why, not the
what.

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

## 4. Operational order and timing

Calendar order, with the actual blocking dependencies between subphases:

```
day 1 morning
  [human]    confirm Vercel and AWS accounts, run vercel login + aws configure
  [human]    paste back: vercel email + aws sts get-caller-identity + ANTHROPIC_API_KEY
  [me]       commit checklist update, drop P6 minimum out of Tier 0
  [me]       commit P3 App Runner config (DEV_AUTH=1, CORS placeholder)
  [human]    click through App Runner service creation in console
  [me]       capture App Runner URL, set CORS_ORIGINS placeholder, smoke /healthz
day 1 afternoon
  [me]       commit P0 Vercel config (.env.example), link project, set Vercel env vars
  [me]       deploy production, capture Vercel URL
  [me]       update App Runner CORS_ORIGINS to the Vercel URL, redeploy
  [me]       smoke an end-to-end upload through the Vercel frontend
day 2 morning
  [me]       commit P9 minimum upload limits + tests, local pytest -q green
  [me]       App Runner redeploys, repeat curl smokes for 413 and 415
  [me]       merge PR #27
```

Total wall-clock budget is roughly one to one and a half engineering days,
dominated by AWS provisioning latency and AWS console click-throughs.
Anthropic API calls are incidental.

---

## 5. Human-only blockers (single concise asks)

Below are the messages I send the user, exactly once per blocker, and then
wait. No improvising around them.

1. P0 unblock: "Run `vercel login` and paste back the email used. Confirm
   Hobby tier." Status: DONE.
2. P3 unblock: "Run `aws configure sso` (or `aws configure`) then paste back
   the output of `aws sts get-caller-identity`. Also paste the production
   `ANTHROPIC_API_KEY` in our private channel."
3. P3 console step: "Click through App Runner service creation in the AWS
   console once, using `apps/api/apprunner.yaml` as the source config and the
   GitHub connection to `retryoos/portside`. Paste the service URL when the
   service is `RUNNING`."

Sentry (was P6 minimum) is deferred to Tier 2; no Sentry blocker exists in
Tier 0. Doppler is Tier 1; the checklist explicitly notes raw env vars in
App Runner and Vercel are acceptable for the demo, so we do not provision
Doppler now.

If any blocker above is missing I stop and wait. I do not invent stand-ins.

---

## 6. Acceptance summary (the four greens that ship the demo)

- A public Vercel URL renders `/cases` after `admin / admin` login.
- A public App Runner URL returns `{"status":"ok"}` on `GET /healthz`.
- An upload from the Vercel frontend reaches `stage=done` with
  `demurrage_due_eur = 84375.0`.
- A 30 MB upload returns 413, a `.docx` upload returns 415, and the
  pytest suite (including the 84,375 gate) is green.

When all four lines are green, Tier 0 is shipped. Tier 1 starts.

---

## 7. Pre-existing issues I noticed but will not fix in this plan

- `apps/api/portside_api/main.py` has two `@app.delete("/voyages/{voyage_id}")`
  registrations. The first is owner-scoped via `Depends(get_current_user)`;
  the second redefines the function without auth and calls
  `store.delete(voyage_id)` without an owner id. Starlette keeps the first
  match, so the auth path wins at runtime, but the dead second route is
  confusing and should be removed in a separate small commit on this same
  branch if time permits, or filed as a follow-up otherwise.
- `apps/api/apprunner.yaml` and several other files contain em dashes
  inherited from before the previous cleanup. They are not in the Tier 0
  diff. I will not regress on this rule: every new line I write here uses
  commas, periods, and colons. A dedicated em-dash sweep is its own PR if
  the user wants it.
- `notes/17-pre-deployment.md` was written for the day-of hackathon AWS
  flex (Amplify + App Runner) and references the older topology. It is not
  wrong, just historical. Tier 0 supersedes it; I am not editing it.

---

## 8. What I report after each subphase commit

A short message, every time, with these five lines:

1. What I did (the commit SHA, the files touched).
2. What is live (the URL).
3. The acceptance evidence (curl trace, screenshot, or pytest excerpt).
4. What is left for the human (paste-back asks, if any).
5. The next subphase I am starting.

If I discover the checklist drifted from reality, the checklist is the bug,
and I fix it on `docs/first-customer-checklist` before continuing.
