# Feature 03 - Both sides of the deal (charterer defense / rebuttal)

## Goal

Today Papership.Ai files a claim from the owner's side. Add the defense side: take a completed
owner claim and produce a charterer rebuttal that concedes the indisputable hours,
contests the weak ones with clause and event citations, and recomputes a reduced quantum.
The reduced number must be derived in deterministic Python, never by the model.

## Why it matters

"Both sides of the deal" on the roadmap. Charterers and the lawyers who defend them are a
second buyer for almost the same product, so this roughly doubles the addressable users
while reusing nearly the entire pipeline.

## What already exists (reuse, do not rebuild)

- `Perspective = "owner" | "charterer"` already threads through the system: `POST /voyages`
  takes a `perspective` form field, and `extractor`, `calculator`, `analyst`, and
  `drafter` all receive it.
- `schemas.py` `FlaggedEvent` already carries BOTH `owner_argument` and
  `charterer_argument`, plus `owner_position_strength` and `incremental_demurrage_eur`.
- `agents/analyst.py` already branches its prompt on `perspective` and re-derives money in
  `_recompute_incremental(...)` (the pattern to copy for the defense swing math).
- `agents/calculator.py` has the deterministic laytime arithmetic to reuse for the
  recomputed quantum.

## The gap this MVP closes

Perspective today mostly changes tone. There is no distinct defense OUTPUT (a rebuttal
that attacks an existing claim and lands on a lower number) and no UI entry point for it.

## Subphases

### Phase 0 - Define the defense output (feature-local model)
In a new module `apps/api/portside_api/defense.py` (keep `schemas.py` frozen), define:
`RebuttalPacket { original_quantum_eur, conceded_eur, contested_eur, reduced_quantum_eur,
rebuttal_letter_markdown, points: list[RebuttalPoint] }` and
`RebuttalPoint { event_id, owner_claim, charterer_response, clause_cited, swing_eur }`.
Acceptance: model imports cleanly and round-trips in a unit test.

### Phase 1 - Defense reasoning + drafting
Add a charterer path that, given the stored `extraction` + `laytime` of an owner claim,
identifies which counted rows the charterer can except (weather, SHEX, WIBON, etc.) and
writes a `RebuttalPoint` for each, then drafts the rebuttal letter. Reuse `analyst.py`
with a defense branch and a new `prompts/rebuttal.md`, and `drafter.py` with a rebuttal
template. The model picks the arguments; it does not pick the numbers.
Acceptance: on the Rotterdam case, the agent emits a point contesting the 4 hour weather
stoppage with a clause-14 citation.

### Phase 2 - Deterministic swing math
Add a Python function `recompute_after_concessions(laytime, won_event_ids) ->
(reduced_quantum_eur, conceded_eur, contested_eur)` that removes the contested hours the
charterer wins, re-sums laytime, and re-multiplies by the rate, reusing the calculator
helpers. This owns every euro figure on the `RebuttalPacket`.
Acceptance: winning the 4 hour weather stoppage reduces 84,375.00 by 4 x 1,875 = 7,500 to
76,875.00.

### Phase 3 - Route and pipeline
Add `POST /voyages/{id}/rebut` that reads the stored owner voyage, runs Phase 1 + Phase 2,
and returns a `RebuttalPacket` (MVP: reuse the stored extraction and laytime, no
re-upload). Optionally also allow `POST /voyages` with `perspective=charterer` to run the
defense variant from fresh PDFs later.
Acceptance: calling `/rebut` on the completed Rotterdam voyage returns a `RebuttalPacket`
with `reduced_quantum_eur = 76875.0`.

### Phase 4 - Frontend
Add a "Defend / rebut" action on a completed case that renders the `RebuttalPacket`:
reduced quantum, conceded versus contested split, the rebuttal points, and the rebuttal
letter. Reuse `ClaimLetter.tsx` and `OutcomeTable.tsx`.
Acceptance: the rebuttal view renders end to end on the Rotterdam case.

### Phase 5 - Tests
Lock the defense math: from the Rotterdam owner fixture, conceding the 41 uncontested
demurrage hours and winning the 4 hour weather stoppage yields `reduced_quantum_eur`
76,875.00. Add to a new `tests/test_defense.py`.
Acceptance: tests pass; the owner-side calculator gate is untouched and green.

## MVP acceptance (end to end)

From the completed Rotterdam owner claim, click Defend and get a rebuttal that concedes
the uncontested hours, contests the 4 hour weather stoppage with a clause citation, and
shows a reduced quantum of EUR 76,875.00. The recomputed number is deterministic and
locked by a test.

## Do NOT touch

The owner-path outputs and their gate. Keep all money deterministic and re-derived in
Python. Announce before any change to frozen `schemas.py`; keep `RebuttalPacket` and
friends in the feature-local `defense.py`.

## Out of scope for MVP

Multi-round negotiation threading, settlement modeling, automatic counter-counter
rebuttals, and a separate charterer document set (reuse the owner's extracted facts).
