# AI Fleet Playbook — using 8 agents with 3 engineers

> Our compute advantage is the playbook. A normal hackathon team has one Claude per engineer. We have ~2.5 Claudes per engineer plus a Gemini for cross-checking. The team that wins May 28th is the one that uses this asymmetry, not the one that ignores it.

The trap is "one agent per engineer." That uses half the fleet. The right model: **workstreams own accounts, people supervise workstreams.** Half the fleet is human-in-loop (engineers coding). The other half is background work that runs while the engineers code.

---

## 1. The fleet

| Account                  | Tier         | Role                                                              |
| ------------------------ | ------------ | ----------------------------------------------------------------- |
| dkall (main gmail)       | Claude Max   | The anchor. Heaviest workload, highest rate limits.               |
| Stamatis                 | Claude Pro   | Primary engineer session — Track [TBD]                            |
| Roman                    | Claude Pro   | Primary engineer session — Track [TBD]                            |
| Panos (invited)          | Claude Pro   | Background workstream                                             |
| Glacdimitris             | Gemini Pro   | Cross-check, red-team, alternative model evaluation               |
| Reserve #1               | Claude Pro   | Spin up if any of the above hits a usage limit                    |
| Reserve #2               | Claude Pro   | Burst capacity for late-day polish                                |

> **Decide on the morning of May 28:** which two engineers use Stamatis + Roman accounts vs the main gmail Max account. Recommendation: the engineer running the heaviest track (probably Track A — the FastAPI + agents 1+2) uses the Max account because of the higher token limits.

---

## 2. Workstream design

Three types of workstream:

### Type 1 — Foreground (human-in-loop, engineer typing)
- **F1 · Track A · API + Agents 1+2** — primary Claude session, used heavily for code generation, debugging, refactoring.
- **F2 · Track B · Agents 3+4 + drafting** — primary Claude session.
- **F3 · Track C · Frontend** — primary Claude session.

### Type 2 — Background (autonomous, periodic check-in)
These run with minimal human supervision. The engineer pings their progress every 30-45 min, gives a course-correction prompt, lets it keep running.

- **B1 · Synthetic data factory** — generates the 5 scenario folders (Piraeus weather + 4 backups), iterates on PDF layouts until they pass the "looks real" smell test. Started at 10:00, fully done by 13:00. **Highest leverage background workstream — without it, the demo has no inputs.**
- **B2 · Prompt iteration** — given fixtures of `ExtractionResult` and `LaytimeResult`, iteratively refines the Agent 3 and Agent 4 prompts until output matches our quality bar. Runs from ~12:00 onwards.
- **B3 · BIMCO letter polish** — given a few real BIMCO claim letter examples (from publicly available sources), iterates on the HTML letter template until it passes the "is this a real letter" smell test.

### Type 3 — Cross-check (different model, second opinion)
- **X1 · Gemini Pro as judge** — evaluates the output of our pipeline against the demo bar. "Does this claim letter pass the smell test of a maritime claims executive? What looks off?" Use 4-6 times across the day.

---

## 3. Account → workstream mapping

| Workstream       | Account              | Why                                                                                |
| ---------------- | -------------------- | ---------------------------------------------------------------------------------- |
| F1 (Track A)     | dkall (Max)          | Heaviest workload — the agent code involves many extraction iterations              |
| F2 (Track B)     | Stamatis             | Prompt-heavy but bounded                                                            |
| F3 (Track C)     | Roman                | UI-heavy, lots of component generation                                              |
| B1 (Data factory)| Panos                | Long-running, autonomous, doesn't compete with engineer needs                       |
| B2 (Prompt iter) | dkall (Max, side session) | Max supports multiple parallel sessions; this runs alongside F1                |
| B3 (Letter polish)| Reserve #1          | Spin up at 14:00 once F2 has a draft template to refine                             |
| X1 (Gemini judge)| Glacdimitris         | Cross-model evaluation — high signal at low cost                                    |
| Burst capacity   | Reserve #2          | Held back; used if any workstream stalls and needs a fresh agent                    |

---

## 4. How to spin up each workstream type

### Foreground (F1/F2/F3)
Each engineer opens Claude Code in their workspace:
```bash
cd ~/Desktop/Code/FlorentHackathon/Source
claude
```
They drive interactively. Read [09-pre-merge-protocol.md](09-pre-merge-protocol.md) for the merge rules.

### Background (B1/B2/B3)

#### Option A — separate terminal, separate `claude` session
Open a second terminal tab, sign in with the account dedicated to that workstream, and give it the brief in one shot:
```bash
claude "You are the synthetic data factory. Read notes/05-synthetic-data.md and notes/01-domain-primer.md. Generate the Piraeus weather dispute scenario PDFs (CP, NOR, SoF) using HTML+weasyprint in synthetic-data/scenarios/athens-weather-dispute/. The PDFs must reconcile against the worked-example numbers in 04-schemas.md. When you're done, generate the four backup scenarios in their respective folders. Check in with me every 30 minutes by writing a status line to STATUS.md in the scenario folder. If stuck, write an UNBLOCK_ME.md with the question."
```

The agent runs until done or stuck. The engineer checks `STATUS.md` periodically.

#### Option B — `run_in_background` Agent invocation (within an existing session)
If you're already in a Claude session and want to launch a background subagent, use the Agent tool with `run_in_background: true`. Useful for spawning workstream B2/B3 from inside F1 once Track A has stabilised.

### Cross-check (X1)
Used reactively, not continuously. When the team wants a second opinion, the operator (whoever holds the Glacdimitris Gemini account) opens Gemini in a browser and pastes:
- The thing being evaluated (a generated letter, a dispute narrative, a UI screenshot)
- A short framing: "Evaluate this for [criterion]. Identify what would look off to a maritime claims executive. Be brutal."

---

## 5. Concrete background-agent briefs (paste these into the agent on the day)

### B1 — Synthetic data factory (paste at ~10:00)

> You are the Portside synthetic data factory. Your job is to produce the demo voyage PDFs.
>
> Read `notes/05-synthetic-data.md` and `notes/01-domain-primer.md` carefully. Then produce these artifacts under `synthetic-data/scenarios/`:
>
> - `athens-weather-dispute/` (PRIMARY — do this first, perfect it, then move on)
>   - `cp.pdf` (2 pages, ASBATANKVOY-style, must contain a weather clause #17 with the 25-knot threshold)
>   - `nor.pdf` (1 page, formal Notice of Readiness)
>   - `sof.pdf` (4 pages, chronological statement of facts at Piraeus with all 9 events from 05-synthetic-data.md)
>   - `weather_record.pdf` (1 page, port authority record showing peak gust 18 knots on 10 May)
>   - `expected.json` (the canonical extraction + calculation + analysis output for the test suite)
> - `nor-tender-dispute/` (backup)
> - `shinc-shex-dispute/` (backup)
> - `congestion-wibon-dispute/` (backup)
> - `on-demurrage-exception/` (backup)
>
> Use HTML + weasyprint to generate each PDF. The script lives at `synthetic-data/generate.py` — write it from scratch. Use a serif font (Crimson Text or similar). Number CP clauses. Use a tabular layout for the SoF.
>
> Critical: the numbers across CP, SoF, and weather_record must all reconcile to produce a demurrage claim quantum of USD 38,400.00 in the primary scenario. Lock that exact number first, then make every document mathematically consistent with it.
>
> Check in every 30 minutes: write a status line to `synthetic-data/STATUS.md` with timestamp, scenario you're on, and any blockers.
>
> If you finish all 5 scenarios with time to spare, do the polish pass:
> - Run the generated PDFs through a 5-second skim test: would a maritime professional believe these are real documents?
> - If yes, generate one alternative version of the primary scenario where the same dispute resolves in the charterer's favor (for the rebuttal-toggle stretch feature).

### B2 — Prompt iteration (paste at ~12:00)

> You are the Portside prompt refinement loop. You are not building the pipeline — Track B is. Your job is to make the output of Agents 3 and 4 read like a senior maritime claims associate wrote it.
>
> Inputs you have access to:
> - `apps/api/portside_api/prompts/analyst.md` (current Agent 3 prompt)
> - `apps/api/portside_api/prompts/drafter.md` (current Agent 4 prompt)
> - `synthetic-data/scenarios/athens-weather-dispute/expected.json` (canonical fixtures)
> - `notes/03-agents.md` (the spec)
> - `notes/01-domain-primer.md` (the domain knowledge)
>
> Workflow per iteration:
> 1. Run Agent 3 against the fixture `LaytimeResult` from `expected.json`.
> 2. Read the output. Compare to a hypothetical real claims associate's output.
> 3. List 3 specific things that sound wrong, vague, or AI-generated.
> 4. Rewrite the prompt to fix those issues.
> 5. Repeat. Do at least 10 iterations.
> 6. Same for Agent 4 once Agent 3 is solid.
>
> Output: each iteration, append to `notes/prompt-iteration-log.md` with the date, version, what changed, and a one-line evaluation.
>
> The final version of each prompt should produce output that:
> - Cites at least one CP clause number per flagged event
> - Cites at least one SoF event ID per flagged event
> - Uses the standard vocabulary (laytime, NOR, SoF, demurrage, SHINC, etc.) correctly
> - Has zero "marketing tone" sentences
> - Reads as if written by a person who has done this for 10 years

### B3 — BIMCO letter polish (paste at ~14:00)

> You are the Portside claim letter polisher. The Agent 4 drafter is producing a letter that follows the template in `apps/api/portside_api/letter_template.html`. Your job is to make the rendered output indistinguishable from a real BIMCO-style demurrage claim letter from a Greek shipping company.
>
> Reference materials (search and read):
> - BIMCO publicly available documentation on demurrage claim letter conventions
> - P&I club educational material on laytime and demurrage
>
> Tasks:
> 1. Read the current letter template HTML and the generated output from a real pipeline run.
> 2. Identify 5-10 specific things that would feel "off" to a real claims executive.
> 3. Improve the HTML template: better typography, correct section ordering, formal salutations, proper letterhead block.
> 4. Render the result via `weasyprint` and screenshot it.
> 5. Repeat until you'd put your name to the letter.
>
> Output: the polished letter template at `apps/api/portside_api/letter_template.html`, plus a brief change log at `notes/letter-polish-log.md`.

### X1 — Gemini judge (manual, reactive)

Use Gemini at these checkpoints:
- **After 13:00 end-to-end run:** "Evaluate this generated dispute narrative against the standard a Greek shipowner's claims executive would apply. What would they cross out with a red pen?"
- **After 15:00 mentor session:** "Here's the demo flow. What's the weakest moment, and how would you strengthen it?"
- **After 17:30 freeze:** "Read this final claim letter. If you're a charterer's lawyer receiving it, what's the first thing you push back on, and is that pushback strong enough to defeat the claim?"
- **18:30, before submission:** "Watch this 5-minute demo recording. Identify the one weakest 15-second window. We can't change the code but we can rehearse the narration — what should change?"

Capture Gemini's responses in `notes/cross-check-log.md`.

---

## 6. Pre-hackathon (May 27 evening)

Each account holder verifies access:
- [ ] dkall logs into Claude Max, confirms multi-session works (open `claude` in two terminals concurrently)
- [ ] Stamatis logs into Claude Pro on his laptop, runs `claude --version`
- [ ] Roman same
- [ ] Panos same; also confirms the team invite worked
- [ ] Glacdimitris confirms Gemini Pro access in a browser
- [ ] Reserve accounts created if not already (use random email aliases on the main gmail with `+claude1`, `+claude2` suffixes)

Each engineer pulls the repo overnight and runs the smoke commands from [09-pre-merge-protocol.md](09-pre-merge-protocol.md) to confirm their laptop can boot the app.

---

## 7. Morning of (08:00–09:45)

In order:
1. **08:00–08:30** — coffee + registration + finding seats. Confirm power outlets at the table.
2. **08:30–09:00** — each engineer opens their primary Claude Code session in the repo. Run `claude` in their workspace. Skim [00-PLAN.md](00-PLAN.md) and their track's spec.
3. **09:00–09:15** — CEO talks. Don't read the docs during the talks; just listen. Re-skim during a coffee break if needed.
4. **09:15–09:45** — second Claude session on each laptop for background work. The B1 brief above is pasted on the laptop that owns the Panos account. Decide who owns which workstream **and write the assignment in a `notes/fleet-assignments.md` file** so it's not in chat.

---

## 8. Per-checkpoint fleet sync (5 min, at each integration point)

At 11:15, 13:00, 15:00, 17:30:

1. Each background workstream operator reads their `STATUS.md` line and reports: "B1 is on scenario 3 of 5, on track." Or "B2 has iterated 6 times, current prompt v0.7 is best."
2. The team decides: keep going, redirect, or kill the workstream.
3. The team checks: any workstream blocked or out of rate limit? If yes, the burst account (Reserve #2) takes over.

This is 5 minutes. Not a meeting. Just a quick verbal round.

---

## 9. Rate limit handling

If an account hits its limit (Claude Pro caps are tight enough that this is possible by mid-afternoon under heavy use):

1. **Pause the offending workstream.** Don't keep retrying; you'll just waste tokens on the same failure.
2. **Migrate the workstream to a reserve account.** Both reserve Pro accounts exist for this.
3. **If the workstream owner was an engineer (F1/F2/F3)**, they switch their Claude Code session login. Their work continues uninterrupted from the next prompt.
4. **If we burn 5 accounts in a day**, we are doing something wrong. Probably we are over-iterating in some loop. Halt the affected workstream and triage.

---

## 10. What we will NOT do with the AI fleet

- We will **not** use AI to write the README, the pitch slides, or anything else that needs to sound like the team. Those are written by us.
- We will **not** let agents write code that nobody reads. The pre-merge protocol in [09-pre-merge-protocol.md](09-pre-merge-protocol.md) applies to agent-authored PRs at higher scrutiny, not lower.
- We will **not** chain agents in a long autonomous loop that builds features end-to-end without checking in. Background agents have narrow remits and check in every 30 minutes.
- We will **not** use the fleet for anything that requires creative or strategic judgment. That's our job.
- We will **not** assume two agents can collaborate by reading each other's output. They can't, reliably. The integration is done by humans at the checkpoints in [07-day-plan.md](07-day-plan.md).
