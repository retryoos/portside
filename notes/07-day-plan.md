# Day Plan — May 28th, 2026

> Twelve effective build hours, three engineers, one demo at 19:00. This is the hour-by-hour. If we are off-plan by an hour, we cut. The cut order is at the end of this doc.
>
> **Pair this doc with [14-parallel-execution-plan.md](14-parallel-execution-plan.md).** This doc describes the day at engineer-grain (Track A/B/C). 14 describes the same day at subphase-grain (one branch per subphase, ~12 parallel branches in Wave 1), so the agent fleet can fan out without colliding on `main`.

---

## Hour 0 — Arrival and setup (08:00 – 09:45)

- 08:00 — Arrive, register, coffee. Get a power outlet and a table where all three can sit together. **Sit together.** Do not split the team across rooms.
- 09:00 — Welcome + CEO talks. Use this time to:
  - Confirm `ANTHROPIC_API_KEY` works on at least two laptops.
  - Pull the repo from `git@github.com:retryoos/portside.git`.
  - Verify `uv`, `pnpm`, Node 22, Python 3.12 are installed.
  - Skim [00-PLAN.md](00-PLAN.md) and [01-domain-primer.md](01-domain-primer.md) together.
  - Decide once: vessel name, owner, charterer, route, dollar figures. Stop bikeshedding the moment the decision is made.

---

## Hour 1 — Skeletons + contract freeze (09:45 – 10:45)

Goal: every track has a runnable skeleton and the schemas are frozen.

| Engineer | Task                                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | `apps/api` skeleton: FastAPI app, `/voyages` POST/GET endpoints returning hard-coded mock `VoyageState`. Pydantic models from [04-schemas.md](04-schemas.md). |
| **B**    | Write the four agent prompts as `.md` files in `apps/api/portside_api/prompts/`. Generate the primary synthetic scenario (one HTML→PDF pass per doc). |
| **C**    | `apps/web` skeleton: Next.js + Tailwind + shadcn/ui. Three-panel layout renders against the mock `VoyageState` from A's endpoint. |

By 10:45 the three apps must be talking to each other end-to-end with dummy data. **This is the integration milestone. Do not let it slip.**

---

## Hour 2 — Agent 1 + UI panels v1 (10:45 – 11:45)

| Engineer | Task                                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | Implement Agent 1 (extractor). Real Anthropic call. Test on the primary scenario PDFs.     |
| **B**    | Implement Agent 2a (LLM classifier) prompt + tool. Test against a hard-coded `ExtractionResult` fixture. |
| **C**    | Real upload flow: drag three PDFs, POST to `/voyages`, poll, render document cards.        |

By 11:45: a real PDF upload should produce a real extraction shown in the left panel.

---

## Hour 3 — Agent 2 arithmetic + Agent 3 (11:45 – 13:00)

| Engineer | Task                                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | Implement Agent 2b (Python arithmetic). Unit tests on the worked-example numbers in [04-schemas.md](04-schemas.md). |
| **B**    | Implement Agent 3 (dispute analyst). Test against a fixture `LaytimeResult`.               |
| **C**    | Render the laytime table from real `LaytimeResult`. Quantum display. Agent steps indicator. |

By 13:00: end-to-end (1 → 2 → 3) is real. Center panel shows real numbers from real PDFs.

---

## Lunch (13:00 – 14:00)

Eat. Decide together: what one thing is most at risk, and what gets cut first?

---

## Hour 4 — Agent 4 + letter export (14:00 – 15:00)

| Engineer | Task                                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | Wire async orchestrator: Agent 2 + Agent 3 in parallel. Single `pipeline.run(voyage_id)`.  |
| **B**    | Implement Agent 4 (drafter). HTML letter template + `weasyprint` PDF export. `/letter.pdf` endpoint. |
| **C**    | Render dispute narrative + executive summary in the right panel. Wire `Generate Letter` button to download PDF. |

By 15:00 the end-to-end demo path should produce a downloadable BIMCO letter.

---

## Hour 5 — Mentor check-in (15:00 – 15:15)

Walk the mentor through one real run. Note their feedback. Decide what to keep, what to ignore, what to cut.

---

## Hour 6 — Polish round 1 (15:15 – 16:30)

Each engineer picks the rough edges in their track.

| Engineer | Probable polish work                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | Real-time pipeline streaming via the polling endpoint. Robust error handling. Retry logic. Prompt cache.        |
| **B**    | Tighten Agent 3 + Agent 4 prompts so the letter reads like a real claims associate wrote it. Add the time-bar statement. |
| **C**    | Contested-row inline expansion. Time-bar badge in the top bar. Better typography. Number formatting.            |

---

## Hour 7 — Backup scenarios + edge cases (16:30 – 17:30)

| Engineer | Task                                                                                       |
| -------- | ------------------------------------------------------------------------------------------ |
| **A**    | Confirm pipeline runs end-to-end on at least one backup scenario.                          |
| **B**    | Improve Agent 4 prose. Test that the letter passes a "does this look like a real letter" smell test. |
| **C**    | Demo dress rehearsal #1: full 5-minute run, time it, fix anything ugly.                    |

By 17:30 the demo path is locked. No new features after this.

---

## Hour 8 — Freeze + dress rehearsal #2 (17:30 – 18:30)

- Run the demo end-to-end three times. Time each. If any takes more than 90s, downshift Agent 4 to Sonnet 4.6.
- **Record a backup video** of one clean run (screen + voiceover). This is the disaster recovery if the live run fails on stage.
- Capture the JSON of one perfect `VoyageState` to a fixture file. If the live run breaks at 19:00, the frontend can be pointed at the fixture as a last resort.
- Pre-stage the three demo PDFs in a folder on the desktop named `01_Anthem_of_Piraeus_voyage_docs`.

---

## Hour 9 — Submission + freshen up (18:30 – 19:00)

- Submit demo (whatever the format is — link / video / repo).
- Do not touch the code after 18:30. If you find a bug, write it down. Do not fix it. The cost of a regression now is higher than the value of a fix.
- Final sanity check: laptop fully charged, presentation cable ready, browser at 100% zoom, Wi-Fi on the venue network is stable.

---

## Hour 10 — Dinner (19:30 – 20:30)

Eat. Decompress. If we are a finalist, rehearse the pitch script from [08-demo-and-pitch.md](08-demo-and-pitch.md) at least twice.

---

## Hour 11 — Finalists pitch (20:30 – 21:00)

Pitch. Win.

---

## Hard rules for the day

1. **Schemas freeze at 10:45.** Any change after that requires all three to agree, verbally.
2. **No new features after 17:30.** Only bug fixes that block the demo.
3. **No new features after 18:30.** Period. Even if it works.
4. **Sit together.** Three engineers in three rooms is three solo projects.
5. **One person owns the demo laptop.** That person does the live demo. They are the only one who touches the keyboard between 19:00 and submission.
6. **The mentor's feedback is input, not orders.** They have not seen [01-domain-primer.md](01-domain-primer.md). If their suggestion contradicts our plan, we discuss it, we don't reflex-implement.

---

## Cut order (if behind schedule)

When we are behind, we cut from the bottom of this list first. **Never cut up the list — always down.**

1. ⬆ Laytime table (the spine of the demo)
2. ⬆ Quantum display (the headline number)
3. ⬆ Agent 1 extraction (no demo without it)
4. ⬆ Agent 2 calculator (the central credibility moment)
5. ⬆ Claim letter PDF (the closing moment)
6. ↕ Agent 3 dispute narrative (cut to one paragraph if needed)
7. ↕ Inline contested-row expansion (fall back to static narrative)
8. ↕ Confidence scores (just say "contested" / "supported")
9. ↕ Time bar badge (just hard-code "OK")
10. ↕ Backup scenarios (only the primary needs to work)
11. ⬇ Word export
12. ⬇ Charterer-side rebuttal toggle
13. ⬇ Streaming letter generation (just render at end)
14. ⬇ Document side-sheet "view excerpt"
15. ⬇ Despatch / partial-day pro-rata polish

If we cut 11–15, the demo is unaffected. If we cut 6–10, the demo is thinner but viable. If we cut 1–5, we have nothing.

---

## Engineer assignment summary

| Track  | Owner | Surfaces                                                                                |
| ------ | ----- | --------------------------------------------------------------------------------------- |
| **A**  | TBD   | FastAPI app, pipeline orchestrator, Agent 1, Agent 2 (LLM + Python), endpoints          |
| **B**  | TBD   | Agent 3, Agent 4, prompts, BIMCO letter template, synthetic data generator              |
| **C**  | TBD   | Entire frontend, three-panel UI, document upload, polling, PDF download, demo polish    |

Assign these names tomorrow morning by 09:45 and don't reshuffle.
