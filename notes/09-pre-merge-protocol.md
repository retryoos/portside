# Pre-Merge Protocol — no CI, no broken main

> We are not running GitHub Actions this hackathon. The discipline that replaces CI is **manual, fast, and per-track**. Read this before opening your first PR on May 28th.

The rule: **main is always demoable.** If the laptop boots, pulls main, runs two commands, and the demo works, we are fine. The protocol below is what keeps that rule true.

---

## 1. Branching

- One long-lived branch: `main`.
- Per change: a short-lived branch named `track-{a|b|c}/{short-slug}` or `fix/{short-slug}`. Examples: `track-a/agent1-extractor`, `track-b/letter-template`, `fix/quantum-rounding`.
- Branch off the latest `main`. Rebase, don't merge, when picking up `main` changes.
- One PR per change. **No direct pushes to main, even fast.** The PR is where the checks happen — even if the reviewer is yourself.
- Squash-merge into main. Keeps history clean for the post-hackathon contest deck.

## 2. The four pre-merge checks (every PR)

Run these in order. Do not skip a step because you "know" it works. The cost of running them is small; the cost of breaking main at 17:00 is the demo.

### Check 1 — It runs locally on your own laptop

| Track | Smoke command                                                                                | What "passes" looks like                                              |
| ----- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| A     | `cd apps/api && uv run uvicorn portside_api.main:app` then `curl localhost:8000/healthz`     | 200 OK                                                                |
| A     | `curl -F cp=@..pdf -F nor=@..pdf -F sof=@..pdf -F perspective=owner localhost:8000/voyages`  | 201 with a `voyage_id`                                                |
| A     | `curl localhost:8000/voyages/{id}` (poll until done)                                         | Returns `VoyageState` with `stage: "done"` and all four sub-objects populated |
| B     | Same as A — your agents are exercised by the same flow                                       | All four agents produce the schema-compliant outputs                  |
| C     | `cd apps/web && pnpm dev` then open `http://localhost:3000`, drag the demo PDFs              | All three panels populate, quantum shows correctly, letter generates  |
| C     | `npx @google/design.md lint apps/web/DESIGN.md` and `npx impeccable detect apps/web/src/`    | Both exit 0; warnings explained in the PR description                 |

If you change a schema, run **both** A and C smoke tests.

**Track C extra requirement:** every frontend PR follows the workflow in [06-frontend.md §0](06-frontend.md#0-required-tooling--read-this-first-every-frontend-agent). `/impeccable shape` before, `/impeccable audit` during, `/impeccable polish` before opening the PR. Paste the audit summary into the PR description. This is non-negotiable — skipping the impeccable pass is the single most reliable way to produce a UI that telegraphs "AI built this."

### Check 2 — The math test passes

```
cd apps/api && uv run pytest tests/test_calculator.py -v
```

This is the only automated test we run. It locks the Agent 2 arithmetic against the worked-example numbers in [04-schemas.md](04-schemas.md). **If it fails, do not merge.** The quantum on the screen is the demo's headline number — getting it wrong is catastrophic.

Anyone touching `calculator.py` or the schemas adds at least one new case to this test.

### Check 3 — One pair of eyes reviewed it

A teammate skims the diff. Not a deep review. They are looking for:
- Schema shape changes (these need a verbal heads-up to the third engineer too)
- Hard-coded paths or secrets
- Console-spam / debug prints left in
- Obvious type or import errors

If the diff is < 30 lines and touches only your track's files, self-review is fine — but say so in the PR description ("self-merged, < 30 lines, track-internal").

### Check 4 — Special rule for agent-written code

If Claude (or any other AI tool) wrote more than ~50 lines of this PR, the author **reads every line out loud** before opening the PR. Half the speed of typing. Triple the catch rate. Agent code looks plausible and confidently wrong; the only defense is reading it.

Specifically watch for:
- Hallucinated imports (a module that doesn't exist)
- Hallucinated SDK methods (e.g., wrong Anthropic SDK call signatures)
- Made-up CP clause language in prompts — every clause cited in a prompt must exist in our actual synthetic CP
- Made-up schema fields — every field set in code must exist in [04-schemas.md](04-schemas.md)
- "Fixed" code that silently swallows exceptions

## 3. Integration checkpoints (full end-to-end, all three tracks)

At each checkpoint, **one engineer (rotating) runs the full demo flow** on the demo laptop and reports pass/fail to the team. Five minutes, max.

| Time   | Checkpoint                                                                  | Pass criterion                                                                |
| ------ | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 11:15  | Schemas frozen, mock end-to-end works                                       | UI renders against API mock; types match Pydantic                              |
| 13:00  | Real extraction + real calculator                                           | Drag PDFs → laytime table fills with correct numbers                          |
| 15:00  | Mentor check-in run                                                         | All four agents complete; quantum visible; one downloadable PDF letter        |
| 17:30  | Feature freeze                                                              | Two consecutive clean demo runs without touching the code in between          |
| 18:30  | Demo lock                                                                   | Backup video recorded; fallback fixture JSON saved; everyone hands off keys   |

If a checkpoint fails: stop, fix it together, do not let people branch off the checkpoint to keep building new things on a broken trunk.

## 4. When main is broken

It will happen at least once. Protocol:

1. **Whoever discovers it announces it in chat.** Stop the world.
2. **Last merge author rolls forward, not back.** They fix the issue with a follow-up PR. Reverting and re-applying loses work.
3. **No new PRs merge into main until the fix is in.** Branch off main if you must keep working, but understand you'll rebase later.
4. **If the fix is taking more than 10 minutes**, the team huddles for 60 seconds and decides: keep fixing, or revert the breaking PR. Time-box ruthlessly.

## 5. Don't merge if any of these are true

- [ ] You haven't run the smoke command for your track
- [ ] The Agent 2 math test is failing (any time, for any reason)
- [ ] You changed a schema and haven't told the other two engineers
- [ ] You added a third-party dependency you didn't discuss with the team
- [ ] You renamed an HTTP route or a JSON field name
- [ ] You committed an `.env` file or any API key

## 6. Things we explicitly do not do during the hackathon

- No code review threads ("nit:", "consider:"). Reviewer either approves or fixes and force-pushes themselves.
- No discussion of style or naming. We agreed in advance: `snake_case` Python, `camelCase` TypeScript, `PascalCase` components. Done.
- No formatter holy wars. `ruff format` on Python, `prettier` on TS, on save in the editor. If your editor doesn't format, fix it before 09:45.
- No long-running branches. If your branch is older than 90 minutes, you are probably out of sync with main.

## 7. The 30-second PR template

PR description fields (paste into the PR body):

```
**Track:** A / B / C
**Touches:** [files or surfaces]
**Schema change?** yes / no  (if yes, post in chat)
**Smoke run output:** [paste curl or describe what you saw]
**Calculator test:** passing / N/A
**Agent-generated?** yes (lines: ~N) / no
```

That's the whole template. Don't write paragraphs.

## 8. After the hackathon (Phase C)

When we set up AWS + Vercel deploy on May 29, we switch on GitHub Actions for:
- `ruff check` + `ruff format --check` on push to any branch
- `tsc --noEmit` on the web app
- The calculator pytest
- A single end-to-end smoke test against a deployed preview environment

But not before May 29. The minutes are too precious on May 28th to spend on green-tick chasing.
