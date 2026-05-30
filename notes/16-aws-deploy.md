# AWS deploy — sponsor flex, off the critical path

> Step-by-step for the day-of AWS deploy. **The local laptop is the demo.** AWS is the "and it's already live on aws.amazon.com right now" flex for the judges. If AWS breaks at 16:00, drop it — the demo is unaffected.

---

## 1. Why

AWS sponsors this hackathon (see `notes/02-architecture.md §12`). Putting Papership.Ai on AWS Amplify + App Runner earns sponsor credit and gives the judges a real public URL to click during the pitch. But the demo runs locally — no DNS, no TLS, no env-var failure modes on stage. The cloud deploy is gravy, never the meal.

## 2. Architecture

```
Browser ──► AWS Amplify Hosting (Next.js 15 frontend)
                    │ HTTPS
                    ▼
            AWS App Runner (FastAPI container, scales to zero)
                    │
                    ▼
            Anthropic API (Sonnet 4.6 primary, Opus 4.7 escape)
```

No database, no S3, no auth, no queues. In-memory state on a single App Runner instance is fine for the day (per `notes/02-architecture.md §12`).

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
   - **Configuration source**: **Use a configuration file** — App Runner picks up `apps/api/apprunner.yaml`.

3. Service settings:
   - **Service name**: `portside-api`.
   - **CPU/memory**: 0.25 vCPU / 0.5 GB (smallest tier — single instance, low traffic).
   - **Auto-scaling**: min 0, max 1 (scale to zero when idle; saves credit).

4. Environment variables (set in console, not committed):
   - `ANTHROPIC_API_KEY` — bind as a **secret** (Secrets Manager or plain env-var; the placeholder in `apprunner.yaml` is `"set-via-console"`).
   - `ANTHROPIC_MODEL_PRIMARY` — `claude-sonnet-4-6` (already in apprunner.yaml; leave as-is).
   - `ANTHROPIC_MODEL_ESCAPE` — `claude-opus-4-7`.
   - `REQUEST_TIMEOUT_S` — `30`.
   - `CORS_ORIGINS` — start at `http://localhost:3000`, update once the Amplify URL is known.

5. Click **Create & deploy**. **First-deploy budget: ~15 min.** Watch the build logs in the App Runner console.

6. Once green, note the App Runner service URL — it looks like `https://<id>.<region>.awsapprunner.com`. Smoke test:
   ```bash
   curl https://<id>.<region>.awsapprunner.com/healthz
   # expect: {"status":"ok"}
   ```

## 4. Frontend → Amplify Hosting

1. Amplify Console → **Host web app** → GitHub. Authorize the `retryoos` org if needed.

2. Repository / branch:
   - **Repo**: `retryoos/portside`.
   - **Branch**: `main` (or the same testing branch as the backend).
   - **App root / monorepo path**: `apps/web`.

3. Build spec: Amplify auto-detects `apps/web/amplify.yml`. Confirm it shows the `npm ci` preBuild and the `npm run build` build step. **Do not edit the lockfile or package manager here** — the committed `package-lock.json` is the source of truth.

4. Environment variables:
   - `NEXT_PUBLIC_API_URL` — `https://<id>.<region>.awsapprunner.com` (from §3 step 6). Set this **before** the first build; Next.js bakes `NEXT_PUBLIC_*` vars in at build time.

5. Click **Save & deploy**. **First-deploy budget: ~30 min** (Amplify cold start is the slow part — provisioning, build, deploy).

6. Once green, note the Amplify domain — typically `https://<branch>.<id>.amplifyapp.com`.

## 5. Post-deploy

Wire CORS now that the Amplify URL exists:

1. App Runner console → service `portside-api` → **Configuration** → edit environment variables.
2. Update `CORS_ORIGINS` to include the Amplify domain, comma-separated:
   ```
   http://localhost:3000,https://<branch>.<id>.amplifyapp.com
   ```
3. App Runner redeploys automatically on config change. Budget ~5 min.

4. Smoke test from the Amplify-hosted page:
   - Open `https://<branch>.<id>.amplifyapp.com` in the browser.
   - Open devtools → Network tab.
   - The frontend should `GET https://<app-runner>/healthz` (or whichever endpoint it pings on load) and get a 200, no CORS error in console.
   - If you see `CORS policy: No 'Access-Control-Allow-Origin'`, the `CORS_ORIGINS` update hasn't propagated — wait 60s and retry.

## 6. Cost guardrail

- **App Runner**: min 0 instances (scale to zero) means we pay only when the service is awake. Cold-start latency on first request is ~5s; acceptable for a sponsor-flex URL no judge will pound on. Expect $5–15/mo against the $200 AWS credit if we leave it running the week after.
- **Amplify Hosting**: free tier covers our traffic comfortably (build minutes + bandwidth). One build per push.
- **Anthropic**: this is the real cost. Sonnet 4.6 calls during a single judge demo are pennies. Don't expose this URL to anything that could loop on it.

## 7. What to do if AWS breaks at 16:00

Drop it. No retro, no debug. The flex is gravy, not the meal — the local laptop demo is unaffected. Mentioning "we have it on AWS too, but we'll demo locally for stability" remains a strong line even without a live URL.

Specifically:
- Don't pull people off the demo path to chase an Amplify build failure.
- Don't pull people off the demo path to chase an App Runner image error.
- The judges' submission form doesn't require a live URL — only the GitHub repo and the Entire dispatch.

If AWS happens to come back green on its own before 19:00, great — point at it during the pitch. If not, ignore it.
