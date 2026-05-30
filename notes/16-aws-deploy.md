# AWS deploy

> **Tier 0 supersedes the original hackathon-era plan.** The current
> deploy topology is **Vercel Hobby (frontend) + AWS App Runner (backend)**,
> not Amplify + App Runner. See
> [`notes/22-tier-0-deploy-plan.md`](22-tier-0-deploy-plan.md) and
> [`first_customer_checklist.md`](first_customer_checklist.md#tier-0--pre-customer-demo-this-week).
> The original Amplify path below (Section 4) remains documented for the
> Tier 3 (P4) migration if AWS-native frontend hosting later becomes a hard
> requirement.

---

## 1. Why

AWS gives us a real public URL for the backend. Vercel gives us the same
for the frontend on a free Hobby tier with GitHub auto-deploy. Together
they cost a few dollars a month against AWS credits plus zero on Vercel
until first-customer traffic.

## 2. Architecture (Tier 0)

```
Browser ──► Vercel Hobby (Next.js 15 frontend, apps/web)
                    │ HTTPS
                    ▼
            AWS App Runner (FastAPI container, scales to zero)
                    │
                    ▼
            Anthropic API (Sonnet 4.6 primary, Opus 4.7 escape)
```

No database (SQLite on App Runner's ephemeral disk), no S3 (filesystem on
the same ephemeral disk), no Cognito (`DEV_AUTH=1`, admin / admin login
per [`notes/21-authentication-stub.md`](21-authentication-stub.md)), no
queues. In-memory + ephemeral state on a single App Runner instance is fine
for the pre-customer demo; Tier 1 swaps these for Cognito + Aurora + S3.

## 3. Backend → App Runner

Source-deploy mode (no ECR push, no docker registry). App Runner builds the `apps/api/Dockerfile` directly from the GitHub repo.

1. Push the branch you want to deploy from:
   - For pre-merge testing: `agent-3/track-d-foundation`.
   - Post-merge: `main`.

2. App Runner console → **Create service**:
   - **Source**: GitHub. Authorize the `retryoos` org if not already connected.
   - **Repository**: `retryoos/portside`.
   - **Branch**: `main` (or the testing branch above).
   - **Source directory**: `apps/api`.
   - **Deployment trigger**: Automatic (rebuilds on push).
   - **Configuration source**: **Use a configuration file**. App Runner picks up `apps/api/apprunner.yaml`.

3. Service settings:
   - **Service name**: `portside-api`.
   - **CPU/memory**: 0.25 vCPU / 0.5 GB (smallest tier; single instance, low traffic).
   - **Auto-scaling**: min 0, max 1 (scale to zero when idle; saves credit).

4. Environment variables (set in console, not committed):
   - `ANTHROPIC_API_KEY`, bind as a **secret** (Secrets Manager or plain env-var; the placeholder in `apprunner.yaml` is `"set-via-console"`).
   - `DEV_AUTH=1`, preserves the admin / admin login through Tier 0. The
     manifest declares this explicitly; the App Runner console can leave it
     as-is.
   - `ANTHROPIC_MODEL_PRIMARY=claude-sonnet-4-6` (already in apprunner.yaml).
   - `ANTHROPIC_MODEL_ESCAPE=claude-opus-4-7`.
   - `REQUEST_TIMEOUT_S=30`.
   - `CORS_ORIGINS`, start at `http://localhost:3000`, update to the Vercel
     production URL once Section 4 lands.

5. Click **Create & deploy**. **First-deploy budget: ~15 min.** Watch the build logs in the App Runner console.

6. Once green, note the App Runner service URL (it looks like `https://<id>.<region>.awsapprunner.com`). Smoke test:
   ```bash
   curl https://<id>.<region>.awsapprunner.com/healthz
   # expect: {"status":"ok"}
   ```

## 4. Frontend → Vercel Hobby (Tier 0)

Vercel is the Tier 0 frontend host. Free Hobby tier, instant deploys on
push, no AWS surface needed. The Amplify path is preserved in
[Section 4b](#4b-frontend--amplify-hosting-tier-3-alternate) for the Tier 3
migration if AWS-native frontend hosting later becomes a hard requirement.

Prereq: `npm i -g vercel` and `vercel login` on the machine driving the
deploy.

1. From the repo root:
   ```bash
   cd apps/web
   vercel link --yes
   ```
   When prompted, scope the project to your Vercel account and pick a new
   project name (suggested: `papership-web`). Vercel writes `.vercel/`
   locally; it is already gitignored in `.gitignore`.

2. Set the production env vars (these are the only two the frontend reads):
   ```bash
   # Generate a long random HMAC secret for the auth-stub cookie.
   AUTH_SECRET_VALUE=$(openssl rand -hex 32)

   # The App Runner URL from §3 step 6.
   APP_RUNNER_URL="https://<id>.<region>.awsapprunner.com"

   printf "%s" "$APP_RUNNER_URL"  | vercel env add NEXT_PUBLIC_API_URL production
   printf "%s" "$AUTH_SECRET_VALUE" | vercel env add AUTH_SECRET production
   ```
   `NEXT_PUBLIC_API_URL` is baked at build time, so it must be set **before**
   the production build. Repeat the same two `vercel env add` lines for the
   `preview` environment if you want preview branches to talk to the same
   backend.

3. Deploy to production:
   ```bash
   vercel --prod
   ```
   First build budget around three to five minutes. Vercel returns the
   production URL on stdout, e.g. `https://papership-web.vercel.app`.

4. Smoke test:
   - Open the URL in a browser. The middleware redirects to `/login`.
   - Sign in with `admin / admin`. You land on `/cases`.
   - Optionally click "Try the demo voyage" for the offline fixture, or
     upload three real PDFs and watch the pipeline reach `done` with the
     EUR 84,375.00 quantum.

## 5. Post-deploy: lock CORS to the Vercel URL

App Runner needs the real Vercel URL in `CORS_ORIGINS` to let browser
requests through.

1. App Runner console → service `portside-api` → **Configuration** → edit
   environment variables.
2. Update `CORS_ORIGINS` to the Vercel production URL (plus localhost for
   local dev):
   ```
   http://localhost:3000,https://papership-web.vercel.app
   ```
3. App Runner redeploys automatically on config change. Budget around five
   minutes.

4. Smoke test from the Vercel-hosted page:
   - Open the Vercel URL in the browser.
   - Open devtools → Network tab.
   - The frontend should `POST <app-runner>/voyages` (after login + upload)
     and get a 201, no CORS error in console.
   - If you see `CORS policy: No 'Access-Control-Allow-Origin'`, the
     `CORS_ORIGINS` update has not propagated yet, wait 60 seconds and
     retry.

### 4b. Frontend → Amplify Hosting (Tier 3 alternate)

Documented for the optional Tier 3 migration (P4). Skip unless AWS-native
frontend hosting becomes a hard requirement (compliance, single bill, VPC).

1. Amplify Console → **Host web app** → GitHub. Authorize the `retryoos` org if needed.
2. Repository / branch:
   - **Repo**: `retryoos/portside`.
   - **Branch**: `main` (or the testing branch).
   - **App root / monorepo path**: `apps/web`.
3. Build spec: Amplify auto-detects `apps/web/amplify.yml`. Confirm it shows the `npm ci` preBuild and the `npm run build` build step. The committed `package-lock.json` is the source of truth; do not switch package managers here.
4. Environment variables:
   - `NEXT_PUBLIC_API_URL`, the App Runner URL from §3 step 6. Set this **before** the first build; Next.js bakes `NEXT_PUBLIC_*` vars in at build time.
   - `AUTH_SECRET`, the same HMAC secret used on Vercel (if you migrate).
5. Click **Save & deploy**. First-deploy budget around thirty minutes (Amplify cold start is the slow part).
6. Once green, note the Amplify domain (typically `https://<branch>.<id>.amplifyapp.com`) and swap it into `CORS_ORIGINS` per Section 5.

## 6. Cost guardrail

- **App Runner**: min 0 instances (scale to zero) means we pay only when the service is awake. Cold-start latency on first request is around five seconds; acceptable for a pre-customer demo URL. Expect $5 to $15/mo against AWS credits if we leave it running for a couple of weeks.
- **Vercel Hobby**: free tier covers our traffic comfortably (builds + bandwidth). One build per push.
- **Anthropic**: this is the real cost. Sonnet 4.6 calls per voyage run are roughly EUR 0.05 to 0.10. Do not advertise this URL to anything that could loop on it.

## 7. What to do if AWS breaks

If App Runner stalls during Tier 0 bring-up, the laptop demo remains the
canonical surface. Investor-grade demos can run locally with `npm run dev`
plus `uv run uvicorn` until App Runner is healthy. The Vercel deploy can
stay up against a placeholder `NEXT_PUBLIC_API_URL` (the "Try the demo
voyage" offline fixture still renders end to end without the backend).

Specifically:
- Do not block the demo waiting for an App Runner image error to resolve.
- Do not block the demo waiting for a Vercel build to finish.
- The Tier 0 acceptance criteria in
  [`notes/22-tier-0-deploy-plan.md`](22-tier-0-deploy-plan.md) §6 are the
  bar; if any of the four greens are red, file a bug and ship the rest.
