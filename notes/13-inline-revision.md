# Inline Highlight-and-Revise — the professional in the loop

> The single highest-leverage stretch feature. Without it the demo says "AI generates a claim letter." With it the demo says "AI drafts the claim letter, the professional refines any sentence in place, and the audit trail is preserved."

The shipping-industry judge will have one implicit question throughout the demo: **"Can I trust this?"** Showing that every line is editable — either by hand or by re-prompting the agent on that specific line — answers that question directly. Papership.Ai is not replacing the claims executive. It is multiplying them.

---

## 1. What the feature does

Two surfaces are **revisable**:

- The **claim letter** in the right panel
- The **dispute narrative** in the right panel

(Optionally, post-hackathon: the inline contested-row explanation in the center panel.)

On either surface:

1. The user selects text with the mouse.
2. A small floating toolbar anchored to the selection appears with one button: **Refine**.
3. Clicking **Refine** opens an inline panel with:
   - Four quick-action chips: **More formal** · **Less aggressive** · **Add clause citation** · **Shorten**
   - A textarea: *"How should this be revised? e.g., cite clause 17 more directly, mention the time bar prominently…"*
   - Two action buttons: **Refine with AI** (primary, brass) and **Edit manually** (secondary)
4. **Refine with AI** → calls the revision micro-agent → loading pulse on the selected span (~1.5s) → new text replaces the selection in place.
5. **Edit manually** → the selected span becomes contenteditable → user types → Enter or click-out saves.
6. Either way, an `✎ edited` mark appears in the margin alongside the revised span. Hovering it shows a tooltip with the revision history (timestamp, source `agent`/`human`, instruction if any).

When the user clicks **Download PDF** or **Download Word**, the export uses the current (revised) text. The audit trail is embedded as a discreet "Revision log" appendix at the end of the document, plus rich metadata in the file properties.

---

## 2. Why this beats the other Tier-1 stretches

| Stretch                              | Demo impact | Effort  | Risk of breakage |
| ------------------------------------ | ----------- | ------- | ---------------- |
| **Inline highlight-and-revise**      | **High** — addresses the implicit "can I trust AI" concern; shows AI-as-collaborator | ~4–5h  | Low — narrow surface, easy to fall back to "edit manually only" |
| Charterer-side rebuttal toggle       | Medium — answers a likely Q&A, but the demo is already owner-side | ~1h    | Low |
| Time-bar countdown going red         | Medium — a credibility signal already baked into the UI | ~30m   | Very low |
| Excel export                         | Medium — claims executives respect it, but not a demo beat | ~1h    | Very low |

Inline revision is the **one feature that adds an entire demo beat**. The others polish what's already there.

Promote it to **Tier 1, slot #1** in [extended_plan.md §9](extended_plan.md#9-stretch-tiers--what-moves-the-needle-if-we-finish-early). Land it first.

---

## 3. Data model — segment IDs and revisions

Every revisable surface is a list of `TextSegment`s with stable IDs. Agent 4 outputs segments directly; the frontend never re-numbers them.

```python
SegmentSurface = Literal["letter", "narrative"]

class TextSegment(BaseModel):
    id: str                                    # "letter-para-3", "narrative-para-2"
    surface: SegmentSurface
    text: str
    revision_history: list["Revision"] = []
    locked: bool = False                       # true for segments that must not be revised
                                               # (the time-bar statement, the quantum line, the demand block)

class Revision(BaseModel):
    timestamp: datetime
    source: Literal["agent", "human"]
    instruction: Optional[str] = None          # populated for agent revisions only
    previous_text: str
    new_text: str
    actor: Optional[str] = None                # post-hackathon: clerk user_id
```

`ClaimPacket` ([04-schemas.md](04-schemas.md#5-claimpacket--output-of-agent-4)) gains two fields:

```python
class ClaimPacket(BaseModel):
    ...
    letter_segments: list[TextSegment]         # was: claim_letter_markdown
    narrative_segments: list[TextSegment]      # was: dispute_narrative_markdown
```

(The `claim_letter_markdown` and `dispute_narrative_markdown` fields are derived from the segments on the fly for backward-compat — keep them for one iteration to avoid breaking Track C's existing renderer.)

**Locked segments** (cannot be revised):

- The dollar quantum line ("We accordingly demand payment of EUR …")
- The time-bar statement (paragraph 4 of the letter)
- The supporting documents list
- Any sentence containing a citation to a specific CP clause number, locked at the citation token level (the surrounding text is revisable, the clause-number token isn't)

The frontend hides the **Refine** toolbar on locked segments.

---

## 4. Backend — the revision endpoint

```
POST /voyages/{voyage_id}/revise
Body:
{
  "surface": "letter" | "narrative",
  "segment_ids": ["letter-para-3"],
  "instruction": "Cite clause 17 more directly and mention the 25-knot threshold.",
  "mode": "agent" | "manual",
  "manual_text": "...optional, required when mode=manual..."
}
Response: 200
{
  "segments": [
    {
      "id": "letter-para-3",
      "surface": "letter",
      "text": "<new text>",
      "revision_history": [
        {
          "timestamp": "2026-05-28T17:42:11+03:00",
          "source": "agent",
          "instruction": "Cite clause 17 more directly...",
          "previous_text": "<old>",
          "new_text": "<new>"
        }
      ]
    }
  ],
  "safety": {
    "quantum_unchanged": true,
    "clauses_preserved": ["17"],
    "events_preserved": ["e6"],
    "warnings": []
  }
}
```

Server-side validation **after** the revision agent responds:
- Parse all `EUR <number>` patterns out of both the old and new text. If any monetary value changed → reject the revision, return 422 with the safety violation, and tell the user "the model attempted to change a monetary value; revision blocked."
- Parse all "clause N" / "§N" patterns. If any were removed or renumbered → reject.
- Parse all event-ID patterns (`e<digit>+`). If any were removed → reject.

This is non-negotiable. A claims letter where the AI silently changed the dollar amount during a re-word would be a catastrophic legal failure.

---

## 5. The revision micro-agent (Agent 5)

### Purpose
Revise one or more `TextSegment`s in place per the user's instruction, preserving the meaning, the legal accuracy, the citations, and any locked values.

### Model
`claude-sonnet-4-6`. Single call, tool-use with `strict: true`. Streaming optional (the segments are small).

### Input (one user message)
- The full surface (all segments concatenated with their IDs as `<segment id="...">...</segment>` markers) — for context. The segments being revised are also flagged with `revising="true"`.
- The selected `segment_ids`.
- The user's `instruction`.
- A summary of the locked values (quantum, time bar date, supporting documents list) — for the agent to know what not to touch.

### System prompt (after the cross-cutting prefix)

```
ROLE: Maritime claims sub-editor.

You receive the full text of a demurrage claim letter or dispute narrative, with each paragraph or sentence wrapped in <segment id="..."> tags. One or more segments are flagged with revising="true". You receive an instruction from a senior claims executive.

Your task: rewrite only the flagged segments according to the instruction. Preserve everything else.

Hard constraints:
- Do not change any monetary value. Every "EUR <number>" appearing in the input must appear unchanged (in value, formatting, and position relative to the surrounding sentence) in your output. If the instruction would require changing a monetary value, return the segment unchanged and explain why in the rejection_reason field.
- Do not remove or renumber any CP clause citation. If the input cites "clause 17", your output must cite "clause 17" (in the same segment, if it was in the same segment).
- Do not remove or change any SoF event ID (e.g., "e6", "e8").
- Do not change the time-bar date or the supporting documents list, even if asked.
- Preserve BIMCO-style formality.

If the instruction conflicts with one of the above, refuse the revision and return the segment unchanged with rejection_reason explaining the conflict in one sentence.

Call record_segment_revisions exactly once with the new text for each revising segment.
```

### Tool definition

```json
{
  "name": "record_segment_revisions",
  "description": "Record the revised text for each segment that was flagged for revision.",
  "input_schema": {
    "type": "object",
    "required": ["revisions"],
    "properties": {
      "revisions": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["segment_id", "new_text", "rejection_reason"],
          "properties": {
            "segment_id": {"type": "string"},
            "new_text": {"type": "string"},
            "rejection_reason": {"type": ["string", "null"]}
          }
        }
      }
    }
  },
  "strict": true
}
```

### Latency target
Under 2 seconds total round-trip. The selected text is small; with prompt caching on the full document and cross-cutting prefix, the marginal call is cheap.

### Prompt cache strategy
Cache the **full surface text** between revisions on the same voyage. Each subsequent revision on the same surface is a cache-hit on the bulk of the input.

---

## 6. Frontend — the components

| Component             | Owner | Responsibilities                                                                 |
| --------------------- | ----- | -------------------------------------------------------------------------------- |
| `RevisableSurface`    | C     | Wraps the letter or the narrative. Renders the segments. Owns selection state.   |
| `SegmentSpan`         | C     | Wraps a single segment. `data-segment-id` attribute. Conditionally contenteditable. |
| `RevisionToolbar`     | C     | Floating tooltip with the **Refine** button. Anchored to the selection rect.     |
| `RevisionPanel`       | C     | The inline form: quick chips + textarea + two action buttons.                    |
| `EditedBadge`         | C     | The small `✎` mark in the margin. Hover shows revision history.                  |
| `useTextSelection`    | C     | Custom hook listening to `selectionchange`. Returns the active selection's segment IDs (or null). |

### Quick-action chip → preset instruction

| Chip                  | Instruction sent to the agent                                                       |
| --------------------- | ----------------------------------------------------------------------------------- |
| More formal           | Make this segment more formal in BIMCO style. Keep the same meaning.                |
| Less aggressive       | Soften the tone of this segment without weakening the legal position.               |
| Add clause citation   | Cite the most relevant CP clause more explicitly in this segment.                   |
| Shorten               | Shorten this segment to one or two sentences while preserving citations.            |

Custom freeform instructions go through the textarea. Either path hits the same endpoint.

### Selection UX details
- Toolbar only appears on selections that fall **inside** revisable segments. Cross-segment selections collapse to "the union of segments touched."
- Toolbar hides automatically on a click elsewhere or on `Escape`.
- Inline panel is positioned below the toolbar if there's room, above if not.
- Manual edit mode adds a 1px brass border (`{colors.tertiary}`) to the editing segment so the user knows where they are typing.

---

## 7. Demo integration — the new Beat 5.5

After **Beat 5 — The claim letter (45s)** in [08-demo-and-pitch.md §1](08-demo-and-pitch.md#part-1--the-5-minute-demo-1900), insert **Beat 5.5 — The professional in the loop (60s)**. Total demo length becomes ~6 minutes, still within window.

> *(Letter is on screen.)*
>
> "And here is where Papership.Ai earns its keep. This letter is a draft. It is not the final word."
>
> *(Highlight the second paragraph — the one describing the weather dispute.)*
>
> "The claims executive reads the draft. Suppose they want the clause citation up front, not buried at the end of the paragraph."
>
> *(Refine toolbar appears. Click it. Inline panel opens. Type into the textarea: "Lead with the citation to CP clause 17.")*
>
> *(Click Refine with AI. Loading pulse for ~1.5s.)*
>
> "The agent rewrites this paragraph only. The dollar amount is locked — it cannot be changed by a re-prompt. The clause citation is preserved. The time-bar statement is locked. Everything else is editable."
>
> *(Paragraph replaces with the revised version. An "edited" mark appears in the margin.)*
>
> "Every revision is logged. Every export carries the audit trail. The claims executive isn't replaced. They are multiplied."

This is the moment where the demo shifts from "look what AI does" to "look what AI lets the human do." It is the most important sixty seconds of the pitch.

---

## 8. Cut order if behind on stretch

Even within this feature, there is a cut path:

1. ⬆ The toolbar showing on selection + **Refine with AI** working on the letter only (90 min)
2. ⬆ Server-side safety validation (quantum / clauses / events preserved) (30 min)
3. ⬆ The `✎ edited` mark in the margin (15 min)
4. ↕ Quick-action chips (30 min) — fall back to freeform textarea only
5. ↕ Manual edit mode (60 min) — fall back to agent-only revision
6. ↕ Narrative also revisable (30 min) — letter-only first
7. ⬇ Revision history hover tooltip (20 min) — log to console only
8. ⬇ PDF export including audit trail (45 min) — current text only
9. ⬇ Cross-segment selection handling (30 min) — single-segment only

The minimum demoable version is rows 1+2+3 in ~2.5 hours. If we have all of Tier 1 plus rows 1-6 here, the demo is gold.

---

## 9. Failure modes and fallbacks

| Failure                                                | Fallback                                                                |
| ------------------------------------------------------ | ----------------------------------------------------------------------- |
| Revision endpoint times out (>5s)                      | Frontend toast: "Agent took too long. Try a manual edit instead."        |
| Agent returns text that fails server-side validation   | 422 → frontend toast: "The agent attempted to change [quantum / clause / event] — revision blocked. Please refine your instruction or use manual edit." |
| User selection crosses a locked segment                | Toolbar hides; tooltip "This part is locked (quantum / time bar / supporting docs)." |
| Cross-segment selection                                | Treat as "revise all touched segments together" — single agent call.    |
| User hits revise twice rapidly                         | Disable the button while a revision is in flight. Queue the second.     |
| Network drops mid-revision                             | Frontend keeps the old text and shows a small error mark; user can retry. |

---

## 10. Implementation order on May 28th (if we get here)

Assume MVP is in by 15:30. Then:

| Block          | Time          | Outcome                                                                                |
| -------------- | ------------- | -------------------------------------------------------------------------------------- |
| Stretch hour 1 | 15:30 – 16:30 | Backend: extend `ClaimPacket` schema with `letter_segments` / `narrative_segments`. Update Agent 4 prompt to output segments. Add `/voyages/{id}/revise` endpoint + the revision micro-agent. Server-side safety validation. |
| Stretch hour 2 | 16:30 – 17:30 | Frontend: `useTextSelection`, `RevisionToolbar`, `RevisionPanel`, segment-IDed rendering of the letter. **Refine with AI** working end-to-end on the letter. |
| Stretch hour 3 | 17:30 – 18:00 | Polish: `EditedBadge`, quick-action chips, manual edit mode, narrative surface. Each is independently land-able — see cut order in §8. |
| Demo prep      | 18:00 – 18:30 | Rehearse Beat 5.5 twice. Pre-load the demo voyage so the letter is already generated on stage. |

Track A (backend) and Track C (frontend) work in parallel on Stretch Hour 1. The contract between them is the new `TextSegment` schema — freeze it by 15:45.

---

## 11. Post-hackathon — what this enables

Inline highlight-and-revise is not just a demo trick. It's the foundation for three Phase C product surfaces:

1. **Counterparty correspondence drafts.** When a charterer replies disputing the claim, Papership.Ai drafts a rebuttal — the claims executive refines it inline before sending.
2. **Internal review.** The senior claims officer reviews the junior's revisions. Every revision has a logged actor (Phase C: Supabase `user_id`). The audit trail becomes a management tool.
3. **The company brain.** Over months, the patterns of what claims executives revise — and how — train a fleet-specific drafting model. Papership.Ai learns the voice of each operator's claims department.

So this is not stretch-for-stretch's-sake. It is the door to the AI-native service motion described in [00-PLAN.md §13](00-PLAN.md#13-beyond-the-hackathon-one-paragraph-for-the-pitch). Build the door now.
