# Track C — Frontend (Roman)

> Your brief. The other two: [18 — Backend core & reasoning (dkall)](18-production-platform-dkall.md) ·
> [19 — AWS deploy/ops/edge (Panos)](19-production-reasoning-panos.md). Read only this one.

**You own:** the web app, plus the ops account that unlocks Doppler for everyone.
Build auth UI against a mock token and features against fixtures/contracts, so you
never wait on a backend merge.

## Shared rules (identical in all three briefs)
- **Subphase = one PR to `main`.** Small, disjoint file set, self-verifying. PRs merge in **any order or by cherry-pick**. No long-lived branch, nobody waits.
- **Build against contracts/mocks, never another track's running code.** Seams: `VoyageStore` Protocol, JWT claim contract (`sub` = user_id), `DATABASE_URL`, S3 bucket env, demo fixtures.
- **`schemas.py` / `web/lib/types.ts` are FROZEN.** New field = single author, announce first, mirror both sides.
- **Two gates never break:** owner `== 84375.0`; charterer `== 76875.0`. Offline `web/public/demo-fixture.json` always works.
- **Stack (AWS credits + sponsor):** Cognito · Aurora Serverless v2 Postgres · S3 · Doppler. Not Supabase/Clerk. Deploy owned by Panos. **Pre-customer frontend host is Vercel Hobby**, not Amplify; the `aws-amplify` JS SDK used in C2 is the Cognito client and is host-agnostic, so this is purely a hosting choice. AWS Amplify hosting is Tier 3 / optional, see [first_customer_checklist.md](first_customer_checklist.md).

## Contracts you consume
- **JWT:** attach the token to API calls; build against a **DEV mock token** until Panos publishes the Cognito client ID / Amplify config.
- **Route shapes:** from dkall — revise-accept (A5), rebut (A6), evidence (A7); from Panos — xlsx (P8), email (P7). Build against the documented request/response + a fixture, swap to live by env when merged.

## Your subphase PRs (each → `main`, disjoint files)
- **C0 — Ops setup (FIRST; unblocks Panos).** Create the free **GitHub Education / Student Developer Pack** account; claim **Doppler free for 1 year** (+ other useful free tiers); share the Doppler workspace with the team. Record claims + expiry in a short note. *Accept:* team has a Doppler project + access.
- **C1 — Edit with AI.** Add `revise()` to `lib/api.ts` (`POST /voyages/{id}/revise`; `ReviseRequest{segment_ids, segments}`/`ReviseResponse` already exist). Wire the existing `ReviseActions/ReviseLetter/RevisePrompt` into the **live** `ClaimScreen`, and call dkall's accept-persist endpoint (A5). *Accept:* live select → refine → accept → persists across reload + in the exported PDF. **Deep spec:** [new_features/01 — Edit with AI](new_features/01-edit-with-ai.md) (you own Phases 0, 1, 3).
- **C2 — Auth UI.** `aws-amplify` Cognito sign-in/up/session; protect routes; account menu; attach JWT. Build vs the mock token until Panos publishes the pool. *Accept:* unauthed → redirect; authed sees only their voyages.
- **C3 — Evidence tab (pairs A7).** Add an Evidence panel to `SourcesTabs.tsx` listing each evidence item (source, observed value, who it supports, link); fixture first. **Deep spec:** [new_features/02 — Research agents](new_features/02-research-agents.md) (Phase 4).
- **C4 — Both-sides toggle (pairs A6).** A "Defend / rebut" action on a completed case; calls `/rebut`; renders the `RebuttalPacket` (reduced quantum, conceded vs contested, points) reusing `ClaimLetter`/`OutcomeTable`; shows the swing **84,375.00 → 76,875.00**. **Deep spec:** [new_features/03 — Both sides](new_features/03-both-sides-defense.md) (Phase 4).
- **C5 — Dashboards.** Real multi-user lists with loading / empty / error states + pagination on `/cases` and `/vessels`.
- **C6 — Web tests (first in repo).** Playwright golden path (upload → done → letter) + Vitest components + an a11y / Lighthouse budget.
- **C7 — Greek i18n toggle.** String-table extraction + a language toggle.

## Do NOT touch
`apps/api/*`, deploy/infra — dkall/Panos. `lib/types.ts` is FROZEN (mirror agreed additions only after the backend PR lands).

## Coordination (non-blocking)
**C0 first** — it unblocks Panos P1/P2. C1↔A5, C3↔A7, C4↔A6, exports/email buttons↔P8/P7. Build vs mock/fixture; swap to live by env/endpoint when the counterpart merges.
