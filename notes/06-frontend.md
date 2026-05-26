# Frontend Spec — the three-panel UI

> The frontend is what the judges see. The backend is what they trust. Both have to be tight, but the frontend is the demo.

---

## 1. Design principles for the day

- **Use shadcn/ui defaults.** No custom theme. No bespoke components. We are not designing a product today — we are showing one.
- **No animations except the agent-step transitions.** Motion costs time and adds failure modes.
- **Typography over chrome.** Big numbers, generous whitespace, monospace for timestamps and dollar amounts.
- **No empty states for things we don't have time to build.** If a screen would be empty, hide it.
- **Demo-mode only.** No login, no settings, no account. The first thing the user sees is the upload zone.

---

## 2. The screen

A single page, three vertical panels on a 16:9 demo laptop (1920×1080):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Portside                              MV Anthem of Piraeus / V-2026-114    │  ← top bar (slim)
├──────────────────────┬─────────────────────────────┬────────────────────────┤
│                      │                             │                        │
│  DOCUMENTS           │  LAYTIME TIMELINE           │  CLAIM PACKET          │
│  (left panel)        │  (center panel)             │  (right panel)         │
│                      │                             │                        │
│  [CP card]           │  Agent steps (top)          │  Executive summary     │
│  [NOR card]          │  Laytime table (middle)     │  Dispute narrative     │
│  [SoF card]          │  Quantum (bottom, big)      │  [Generate Letter] btn │
│                      │                             │  Letter preview        │
└──────────────────────┴─────────────────────────────┴────────────────────────┘
```

Proportions: 25% / 45% / 30%.

---

## 3. Top bar

- **Left:** Portside wordmark.
- **Center:** Voyage identifier — vessel name, voyage number, route. Empty before upload.
- **Right:** Owner | Charterer toggle (defaults to Owner — for the demo we stay on Owner).
- **Far right:** "Time bar: 88 days remaining" badge when there is a loaded voyage. Green if > 30 days, amber if < 30, red if past. **This badge is the one piece of UX a real maritime user will recognize as competent.**

---

## 4. Left panel — DOCUMENTS

### Empty state
A single dropzone covering the panel: "Drop three voyage documents here — Charter Party, Notice of Readiness, Statement of Facts." Below it, a "Try the demo voyage" button that loads the prepared scenario.

### Loaded state
Three cards stacked vertically:

```
┌──────────────────────────────────────┐
│  CHARTER PARTY                       │
│  ASBATANKVOY · CP dated 12 Apr 2026  │
│  Laytime: 72h SHINC                  │
│  Demurrage: USD 48,000/day           │
│  Clauses: WIBON, WIFPON, §17 weather │
│  [view excerpt]                      │
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  NOTICE OF READINESS                 │
│  Tendered 08 May 07:00 LT            │
│  Accepted 08 May 07:00 LT            │
│  Free pratique 08 May 08:30 LT       │
│  [view document]                     │
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  STATEMENT OF FACTS                  │
│  Port: Piraeus (Europe/Athens)       │
│  9 events recorded                   │
│  [view full SoF]                     │
└──────────────────────────────────────┘
```

The `[view ...]` links open a side sheet showing the extracted text and (optionally) the source PDF. Cuttable if behind.

---

## 5. Center panel — LAYTIME TIMELINE

This is the panel the judge will look at hardest.

### Agent steps (top, slim)
A horizontal step indicator that lights up as each agent completes:

```
[✓ Extract docs]  →  [✓ Calculate laytime]  →  [● Analyze disputes]  →  [○ Draft claim]
```

Replaces a loading spinner. Each step shows a one-line description while active ("classifying 9 SoF events against CP clauses…").

### Laytime table (middle, scrollable)

```
┌────────────────────┬────────────────────┬──────┬─────────┬─────────────┬─────────────────────────────┐
│ From               │ To                 │  Hrs │ Counts? │ Running tot │ Reason                      │
├────────────────────┼────────────────────┼──────┼─────────┼─────────────┼─────────────────────────────┤
│ 08 May 13:00 LT    │ 09 May 02:00 LT    │ 13.0 │   yes   │  13.0       │ Laytime — pre-berth         │
│ 09 May 02:00 LT    │ 09 May 04:00 LT    │  2.0 │   yes   │  15.0       │ Laytime — at berth          │
│ 09 May 04:00 LT    │ 10 May 11:00 LT    │ 31.0 │   yes   │  46.0       │ Laytime — discharge ops     │
│ 10 May 11:00 LT    │ 10 May 22:00 LT    │ 11.0 │ ⚑ no?   │  46.0       │ Contested — weather, §17    │  ← row flagged
│ 10 May 22:00 LT    │ 11 May 18:30 LT    │ 20.5 │   yes   │  66.5       │ Laytime — discharge ops     │
│ 11 May 18:30 LT    │ 12 May 12:00 LT    │ 17.5 │   yes   │  84.0 / 89.5│ ON DEMURRAGE                │  ← row styled red
└────────────────────┴────────────────────┴──────┴─────────┴─────────────┴─────────────────────────────┘
```

Contested rows are styled with a left border in amber and a small flag icon. Click expands an inline section showing the dispute argument (this is the "winning moment" of the demo):

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ⚑  Weather exception not supported by CP clause threshold                  │
│                                                                            │
│ Charterer claims 11 hours of weather stoppage on 10 May 2026. CP clause   │
│ 17 admits weather exceptions only when sustained wind speeds exceed 25     │
│ knots. The port authority weather record for that date shows peak gusts   │
│ of 18 knots and no rain at the relevant times.                            │
│                                                                            │
│ Owner's position: 88% confidence                                           │
│ Incremental recoverable demurrage: USD 22,000                              │
│ Citations: CP clause 17; SoF event e6                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### Quantum (bottom, big)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│           DEMURRAGE DUE TO OWNERS                                          │
│           USD 35,000.00                                                    │  ← 64px display, mono
│                                                                            │
│           Laytime allowed 72h · Used 89.5h · On demurrage 17.5h            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

When the dispute resolves in owner's favor, the figure ticks up to reflect the incremental amount. (Or simpler: just show the final figure. Cuttable.)

---

## 6. Right panel — CLAIM PACKET

### While pipeline is running
A subtle skeleton state. No spinner. The center panel's agent step indicator carries the loading affordance.

### When done
- **Executive summary block.** Three lines, generated by Agent 4.
- **Dispute narrative.** Three to five paragraphs, scrollable. Generated by Agent 4.
- **`Generate Claim Letter`** button. Primary color, big.
- **Letter preview area.** Empty until the button is clicked. Then it fills with the rendered HTML preview of the BIMCO letter, with `Download PDF` and `Download Word` buttons above it.

### Letter preview
The HTML preview is rendered inline (not as an embedded PDF iframe) so we can stream it during generation. The download buttons fetch `/voyages/{id}/letter.pdf` and `/voyages/{id}/letter.docx`.

---

## 7. Components to build

| Component               | Owner | Notes                                              |
| ----------------------- | ----- | -------------------------------------------------- |
| `Topbar`                | C     | Voyage label, perspective toggle, time-bar badge   |
| `Dropzone`              | C     | Three-file drop with file-type detection           |
| `DocumentCard`          | C     | CP / NOR / SoF summary card                        |
| `AgentSteps`            | C     | The 4-step progress indicator                      |
| `LaytimeTable`          | C     | The center table with expandable contested rows    |
| `QuantumDisplay`        | C     | The big number block                               |
| `ExecutiveSummary`      | C     | The right-panel three-line summary                 |
| `DisputeNarrative`      | C     | Markdown rendered paragraphs                       |
| `LetterPreview`         | C     | Inline HTML letter preview + download buttons      |
| `apiClient` (lib)       | C     | Typed fetch wrapper mirroring [04-schemas.md](04-schemas.md) |

All UI surface = Track C's responsibility. Tracks A and B do not touch the frontend.

---

## 8. Cut order for the frontend (if behind)

1. Word export button (PDF only)
2. Document side-sheet "view excerpt" feature
3. Inline expansion of contested rows — fall back to static dispute narrative in the right panel
4. Time-bar badge (just say "Time bar: OK" if logic is half-built — don't compute days)
5. Streaming letter preview — render after generation completes

Order is from least-noticed-when-missing to most. Do not cut the laytime table, the quantum display, or the BIMCO letter PDF — those are the demo.

---

## 9. The demo polish list

Before 18:30:
- [ ] Replace any "Lorem ipsum" with real data
- [ ] Numbers are formatted with thousands separators and two decimals (`USD 35,000.00`)
- [ ] Timestamps are uniform (`08 May 13:00 LT`)
- [ ] No console errors
- [ ] One reload between runs to confirm clean state
- [ ] Browser zoom set to 100%
- [ ] Browser at full screen on the demo laptop
- [ ] Wallpaper / dock cleaned up on the demo laptop
