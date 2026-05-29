# Feature 01 - Edit with AI (inline rewrite on the live claim)

## Goal

On the live case detail page (`/cases/[id]`), let a user select a sentence or paragraph
in the claim letter (or dispute narrative) and ask AI to rewrite it in place. The
existing server-side safety gate must still reject any rewrite that changes a monetary
value or drops a clause or event citation. Crucially, an accepted rewrite must persist
back into the stored voyage so it survives a reload and flows into the PDF export.

## Why it matters

It is the most concrete, demo-able item on the roadmap and it turns the claim from a
read-only artifact into something a claims executive can shape, without ever letting the
AI touch the numbers. It is also the cheapest to build because most of the backend is
already done.

## What already exists (reuse, do not rebuild)

- `apps/api/portside_api/reviser.py`: the revise micro-agent, the wire models
  (`ReviseRequest`, `ReviseResponse`, `RevisedSegment`, `SafetyReport`), and the pure
  stdlib safety validator `validate_revision(old, new)` that locks EUR values, `clause N`
  citations, and `eN` event ids.
- `apps/api/portside_api/main.py`: route `POST /voyages/{id}/revise` returns
  `ReviseResponse`, or HTTP 422 with the safety report when a rewrite is blocked.
- `apps/api/portside_api/prompts/reviser.md`: the reviser prompt.
- `apps/api/tests/test_reviser.py`: existing safety-gate tests.
- Frontend demo-only components: `ReviseLetter.tsx`, `ReviseActions.tsx`,
  `RevisePrompt.tsx`, and the standalone page `apps/web/app/revise/page.tsx`. These run on
  the static demo fixture and show the intended UX (segment the letter, select, prompt,
  preview, accept).
- `apps/web/components/ClaimLetter.tsx`: renders the letter on the live case detail.
- `apps/web/lib/api.ts`: has `createVoyage`, `getVoyage`, `pollVoyage`, `setVoyageStatus`.

## The gaps this MVP closes

1. `api.ts` has no `revise()` client and `/cases/[id]/page.tsx` never calls revise. The
   feature only exists on the disconnected `/revise` demo page.
2. `POST /voyages/{id}/revise` returns the rewrite but does NOT write it back into the
   stored `VoyageState.packet`. So an accepted edit is lost on the next poll and never
   reaches `ExportPdfButton`.
3. The live letter is not segmented into addressable units, so a text selection cannot be
   mapped to `segment_ids` the way `ReviseRequest` expects.

## Subphases

### Phase 0 - Segment the live letter (frontend)
Render `packet.claim_letter_markdown` (and `dispute_narrative_markdown`) as addressable
segments with stable ids (`l0, l1, ...` for the letter, `n0, n1, ...` for the narrative),
splitting on paragraph or sentence boundaries. Mirror the segmentation already used in
`ReviseLetter.tsx`. A text selection resolves to one or more segment ids.
Acceptance: selecting text in `ClaimLetter` on a live case yields the correct segment ids.

### Phase 1 - API client + types (frontend)
Add `revise(voyageId, body: ReviseRequest): Promise<ReviseResponse>` to `api.ts`. Add the
matching TypeScript types to `apps/web/lib/types.ts`, mirroring the `reviser.py` wire
models. On a 422, parse `detail.safety.warnings` and return them so the UI can show why a
rewrite was refused.
Acceptance: a unit/manual call to `revise()` round-trips against a running backend.

### Phase 2 - Persist accepted revisions (backend)
Make an accepted revision update the stored packet. Either extend the existing route or
add `POST /voyages/{id}/revise/apply`. On accept, patch `packet.claim_letter_markdown` /
`packet.dispute_narrative_markdown` by substituting the revised segment text, via
`store.patch(...)`. Verify `apps/api/portside_api/storage.py` `patch` can set nested
packet fields; extend it if it only supports `stage`. Keep the safety gate in front of
any persistence so a blocked rewrite never reaches the store.
Acceptance: after an accepted revise, `GET /voyages/{id}` returns the updated letter text.

### Phase 3 - Wire the UX into the live case detail
In `/cases/[id]`, add a selection affordance on `ClaimLetter`: select text, type an
instruction, call `revise()`, show the proposed text against the original, and offer
Accept or Discard. On Accept, call the Phase 2 persistence path; the updated packet flows
back through the existing poll and into `ExportPdfButton`. Surface `safety.warnings` when
blocked, calmly and inline.
Acceptance: the full select to rewrite to accept loop works on a real case, not the demo page.

### Phase 4 - Tests and gate
Extend `tests/test_reviser.py`: an accepted revision mutates the stored packet; a blocked
revision (tries to change `EUR 84,375.00`, or drops `clause 14` or an `eN` id) leaves the
stored packet unchanged and returns 422 with warnings.
Acceptance: tests pass; the calculator gate (`test_calculator.py`) is untouched and green.

## MVP acceptance (end to end)

On the live Rotterdam case: select a sentence in the letter, instruct "make this more
formal", and see it rewritten in place. A rewrite that attempts to alter EUR 84,375.00 or
drop clause 14 is rejected with a visible reason. The accepted letter persists across a
reload and exports correctly to PDF.

## Do NOT touch

The deterministic calculator and its gate, the four pipeline agents, and the frozen money
fields. Keep all new wire models out of `schemas.py` (follow the local-models pattern in
`reviser.py`).

## Out of scope for MVP

Revision history / undo stack, multi-user editing, token-by-token streaming of the
rewrite, and revising anything other than the letter and narrative.
