# Frontend Spec — the three-panel UI

> The frontend is what the judges see. The backend is what they trust. Both have to be tight, but the frontend is the demo.

---

## 0. REQUIRED TOOLING — read this first, every frontend agent

> **This section is mandatory. Every human and every AI agent doing any frontend work — Track C primary, background polish workstreams, mentor-feedback-driven fixes, last-minute demo polish — uses both of these. No exceptions. If you skip them you will produce a SaaS-template UI that telegraphs "AI built this in 12 hours," which is the one thing we cannot afford.**

### 0.1 `DESIGN.md` — the design tokens contract

The Portside design system lives at [apps/web/DESIGN.md](../apps/web/DESIGN.md). It is a [google-labs-code/design.md](https://github.com/google-labs-code/design.md) spec file: YAML front-matter for tokens (colors, typography, spacing, components) and Markdown for rationale.

**Every Tailwind class you write maps to a token in that file.** If you find yourself reaching for `bg-gray-100` or `text-blue-600`, you are doing it wrong — go back to `apps/web/DESIGN.md`, find the right token, and use the corresponding Tailwind v4 CSS variable (`bg-surface-muted`, `text-primary`, etc.). If a token doesn't exist for what you need, the answer is almost always to use an existing one differently, not to add a new color.

Validate the file with the linter:

```bash
cd apps/web
npx @google/design.md lint DESIGN.md
```

This catches: broken token references, contrast-ratio fails, orphan tokens, missing primary, out-of-order sections. Run it after any change to `DESIGN.md`.

Export the tokens to a Tailwind v4 theme block (done once during the morning skeleton, regenerated only if `DESIGN.md` changes):

```bash
npx @google/design.md export --format css-tailwind DESIGN.md > app/theme.css
```

Then `@import "./theme.css";` from `app/globals.css`. After this every token in `DESIGN.md` is available as a Tailwind utility.

### 0.2 `/impeccable` — the design-quality skill

[pbakaus/impeccable](https://github.com/pbakaus/impeccable) is a Claude Code skill with 23 frontend-design commands and 27 deterministic anti-pattern rules. It is **already available** in our Claude Code sessions as the `impeccable` skill. Every frontend agent invokes it at three points:

| When                          | Command                       | Why                                                                       |
| ----------------------------- | ----------------------------- | ------------------------------------------------------------------------- |
| **Before** typing any new UI  | `/impeccable shape <surface>` | Plans UX/UI before code. Reads `DESIGN.md`. Prevents reinvention.         |
| **After** writing a component | `/impeccable audit <surface>` | Runs the deterministic anti-pattern checks + the LLM critique pass.       |
| **Before** opening a PR       | `/impeccable polish <surface>`| Final pass, design-system alignment, shipping readiness.                  |

For specific issues, the more targeted commands replace ad-hoc fixes:
- `/impeccable typeset <surface>` — fix fonts, hierarchy, sizing
- `/impeccable layout <surface>` — fix layout, spacing, visual rhythm
- `/impeccable harden <surface>` — add error handling, i18n, text-overflow, edge cases
- `/impeccable quieter <surface>` — tone down anything that became too loud
- `/impeccable distill <surface>` — strip to essence when the screen feels busy

The anti-patterns impeccable catches that we will *otherwise* fall into:

- Inter for everything (we use Fraunces + IBM Plex Sans + JetBrains Mono — see [`DESIGN.md`](../apps/web/DESIGN.md))
- Gray text on colored backgrounds (kills contrast)
- Pure black/gray (always tint — our `primary` is `#0A1929`, not `#000000`)
- Cards nested in cards (the left-panel document cards live directly on paper)
- Bounce / elastic easing (we use linear and ease-out only)
- Purple-to-blue gradients (we have no gradients)
- The rounded-square icon tile above every heading (we have no icon tiles)
- Skipped heading levels (h1 → h3 is a bug)
- Cramped padding and tiny touch targets

Run the deterministic detector before each PR:

```bash
cd apps/web
npx impeccable detect src/
```

It scans for these patterns without needing an API key. Exit code is non-zero if it finds issues.

### 0.3 The mandatory frontend workflow

```
1. Read this doc (06-frontend.md).
2. Read apps/web/DESIGN.md.
3. /impeccable shape <surface>   ← before typing
4. Build the component using tokens from DESIGN.md.
5. /impeccable audit <surface>   ← after the component renders
6. Fix any findings.
7. npx impeccable detect apps/web/src/<path>   ← deterministic sweep
8. /impeccable polish <surface>  ← before opening the PR
9. Open the PR. Paste the audit / polish summary into the PR description.
```

If you skip step 3, you will reinvent decisions DESIGN.md already made. If you skip step 5, your component will ship with at least one of the anti-patterns above. We do not have time to redo work — front-load the skill calls.

---

## 1. Design principles for the day

These are downstream of section 0; if there is ever a conflict, `DESIGN.md` and `/impeccable` win.

- **Use the tokens.** Not Tailwind defaults, not arbitrary hex values. Tokens or nothing.
- **Use shadcn/ui's structure, override its tokens.** shadcn components give us a structurally-correct starting point. We restyle them via the `DESIGN.md`-derived theme — we do not accept shadcn's default Inter/zinc look.
- **Typography is the design.** Fraunces serif for the three panel labels and the few headings; IBM Plex Sans for body; JetBrains Mono for every number. That's the whole visual identity.
- **One brass accent per viewport.** The `Generate Claim Letter` button is brass. The `New Voyage Claim` button is brass. No third primary button on any screen.
- **No animations except agent-step transitions and color shifts on hover.** Motion is a state-change tool, not decoration.
- **No empty states for things we don't have time to build.** If a screen would be empty, hide it.

---

## 2. The screen

A single page, three vertical panels on a 16:9 demo laptop (1920×1080):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Portside                              MV Anthem of Piraeus / V-2026-114    │  ← top bar (slim, warm paper)
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

Proportions: 25% / 45% / 30% at `lg:` and above. Below `md:`, panels collapse to a tab switcher with the quantum sticky at the bottom.

Background: `{colors.neutral}` (warm paper). Panels sit directly on the background — no parent card.

---

## 3. Top bar

- **Left:** "Portside" set in `h2` (Fraunces). No logo.
- **Center:** Voyage identifier — vessel name in `h3`, voyage number in `label-caps` `{colors.secondary}` below. Empty before upload.
- **Right:** Owner | Charterer toggle (`label-caps`, default Owner).
- **Far right:** Time-bar countdown badge. Uses `badge-timebar-ok` / `badge-timebar-warning` / `badge-timebar-danger` from `DESIGN.md`. Format: "Time bar: 88 days".

The time-bar badge is the single most credible-feeling detail in the UI; do not let it slip in polish priority.

---

## 4. Left panel — DOCUMENTS

### Empty state
A single dropzone covering the panel. Copy in `body`:

> Drop three voyage documents here — Charter Party, Notice of Readiness, Statement of Facts.

Below, a `button-secondary`: **Try the demo voyage**.

The dropzone border uses `{colors.border}` 1px dashed; no shadow.

### Loaded state
Three `card-muted` blocks (these are evidence, not the active surface), stacked with `{spacing.md}` gap. Each:

```
┌──────────────────────────────────────┐
│  CHARTER PARTY              [label-caps {colors.secondary}]
│  ASBATANKVOY · CP dated 12 Apr 2026  [body {colors.primary}]
│  Laytime: 72h SHINC                  [body-sm]
│  Demurrage: USD 48,000/day           [body-sm, JetBrains Mono]
│  Clauses: WIBON, WIFPON, §17 weather [body-sm]
│  [view excerpt]                      [body-sm link, {colors.tertiary}]
└──────────────────────────────────────┘
```

Same shape for NOR (with tender / accept times) and SoF (with port, timezone, event count).

`[view excerpt]` opens a side sheet showing the extracted text. Cuttable.

---

## 5. Center panel — LAYTIME TIMELINE

This is the panel the judge looks at hardest. Sits on `{colors.surface}` (white) so the table reads with maximum clarity.

### Agent steps (top)
A horizontal step indicator. Each step: a `label-caps` title, a circle/check icon to the left, a one-line description below in `body-sm` `{colors.secondary}` when active.

```
[✓ Extract docs]  →  [✓ Calculate laytime]  →  [● Analyze disputes]  →  [○ Draft claim]
```

Completed steps: `{colors.success}` icon. Active: `{colors.tertiary}`. Pending: `{colors.border}` outline.

### Laytime table (middle, scrollable)

Column headers in `label-caps` `{colors.secondary}`. Body rows in `body` for descriptions, `mono` for the From / To / Hours / Running columns. Every number column right-aligned.

```
FROM              TO                HRS    COUNTS   RUNNING TOT   REASON
─────────────────────────────────────────────────────────────────────────────
08 May 13:00 LT   09 May 02:00 LT   13.0   yes      13.0          Laytime — pre-berth
09 May 02:00 LT   09 May 04:00 LT    2.0   yes      15.0          Laytime — at berth
09 May 04:00 LT   10 May 11:00 LT   31.0   yes      46.0          Laytime — discharge ops
10 May 11:00 LT   10 May 22:00 LT   11.0   ⚑ no?    46.0          Contested — weather, §17    ← table-row-contested
10 May 22:00 LT   11 May 18:30 LT   20.5   yes      66.5          Laytime — discharge ops
11 May 18:30 LT   12 May 12:00 LT   17.5   yes      84.0 / 89.5   ON DEMURRAGE                ← table-row-demurrage
```

- Contested rows: `table-row-contested` background, 1px left border in `{colors.contested}`.
- Demurrage rows: `table-row-demurrage` background.
- Hairlines between rows in `{colors.border}`. No zebra striping.

Click a contested row → inline expansion below the row, in `card-muted` style:

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
│ Incremental recoverable demurrage: USD 22,000.00                           │
│ Citations: CP clause 17; SoF event e6                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### Quantum (bottom)

The gravitational center of the screen. Set the number in `mono-quantum` (JetBrains Mono, 60px, weight 500). Set the label above in `label-caps` `{colors.secondary}`. Set the sub-line below in `body-sm` `{colors.secondary}`.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│           DEMURRAGE DUE TO OWNERS                                          │
│           USD 38,400.00                                                    │  ← mono-quantum
│                                                                            │
│           Laytime allowed 72h · Used 89.5h · On demurrage 17.5h            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Right panel — CLAIM PACKET

Sits on `{colors.surface-muted}` (slightly darker paper) to set it apart from the center.

### While the pipeline is running
Skeleton state using `{colors.border}` placeholders. No spinner. The agent step indicator in the center panel carries the loading affordance.

### When done
- **Executive summary block** — three lines in `body`, generated by Agent 4.
- **Dispute narrative** — `h2` heading "Dispute summary", then paragraphs in `body`, scrollable.
- **`Generate Claim Letter`** — full-width `button-primary` (brass). The visual anchor of this panel.
- **Letter preview area** — empty until the button is clicked. Then renders the HTML letter inline (not as an iframe — we want streaming visible). Two `button-secondary` above: `Download PDF`, `Download Word`.

The letter preview uses the same typography tokens as the product itself — Fraunces for the recipient block and "Re:" line, IBM Plex Sans for the body, JetBrains Mono for monetary amounts in the calculation summary.

---

## 7. Components to build

| Component               | Owner | Notes                                                                          |
| ----------------------- | ----- | ------------------------------------------------------------------------------ |
| `Topbar`                | C     | Voyage label, perspective toggle, time-bar badge                                |
| `Dropzone`              | C     | Three-file drop with file-type detection                                        |
| `DocumentCard`          | C     | CP / NOR / SoF summary card on `card-muted`                                     |
| `AgentSteps`            | C     | The 4-step progress indicator                                                   |
| `LaytimeTable`          | C     | The center table with `table-row-contested` and `table-row-demurrage` variants  |
| `ContestedExpansion`    | C     | Inline expansion inside the table on contested-row click                        |
| `QuantumDisplay`        | C     | The big number block, `mono-quantum`                                            |
| `ExecutiveSummary`      | C     | The right-panel three-line summary                                              |
| `DisputeNarrative`      | C     | Markdown rendered paragraphs                                                    |
| `LetterPreview`         | C     | Inline HTML letter preview + download buttons                                   |
| `TimebarBadge`          | C     | Three-color status chip                                                         |
| `apiClient` (lib)       | C     | Typed fetch wrapper mirroring [04-schemas.md](04-schemas.md)                    |
| `RevisableSurface`      | C     | **Tier 1 stretch.** Wraps the letter or narrative, segment-IDed, selection-aware. See [13-inline-revision.md](13-inline-revision.md). |
| `RevisionToolbar`       | C     | Tier 1 stretch. Floating tooltip with **Refine** button on selection.            |
| `RevisionPanel`         | C     | Tier 1 stretch. Quick chips + instruction textarea + Refine/Edit actions.        |
| `EditedBadge`           | C     | Tier 1 stretch. The `✎` mark in the margin of revised segments.                  |

All UI = Track C. Tracks A and B do not touch frontend code.

---

## 8. Frontend PR checklist

For any PR that touches `apps/web/`:

- [ ] I ran `/impeccable shape <surface>` before typing the new UI (or I noted in the PR why this was a one-line fix that didn't warrant it).
- [ ] I used tokens from `apps/web/DESIGN.md`. No raw hex values in component code.
- [ ] I ran `npx @google/design.md lint apps/web/DESIGN.md` if I edited the tokens — zero errors.
- [ ] I ran `npx impeccable detect apps/web/src/` — output pasted in the PR description, all issues addressed or explained.
- [ ] I ran `/impeccable audit <surface>` — findings pasted, action taken on each.
- [ ] I ran `/impeccable polish <surface>` before merging.
- [ ] No new font family added. No new top-level color added.
- [ ] Mobile breakpoint: I resized the browser to <768px and confirmed the panels collapse to a tab switcher without overflow.
- [ ] No console errors and no console warnings.

The pre-merge protocol in [09-pre-merge-protocol.md](09-pre-merge-protocol.md) Check 1 already requires a track smoke test; this is the additional Track-C surface-area check.

---

## 9. Cut order for the frontend (if behind)

When we are behind, we cut from the bottom of this list first. **Never cut up the list — always down.**

1. ⬆ Laytime table (the spine of the demo)
2. ⬆ Quantum display (the headline number)
3. ⬆ Agent step indicator
4. ⬆ Claim letter PDF download
5. ↕ Contested-row inline expansion (fall back to static narrative in the right panel)
6. ↕ Time-bar badge color logic (just hard-code "OK")
7. ↕ Document side-sheet "view excerpt"
8. ⬇ Word export button (PDF only)
9. ⬇ Charterer-side perspective toggle
10. ⬇ Streaming letter generation (render after completion)
11. ⬇ Mobile tab-switcher behavior — fall back to a simple stacked layout

Do not cut anything above row 6 unless the demo is on fire.

---

## 10. The demo polish list

Before 18:30:
- [ ] `npx @google/design.md lint apps/web/DESIGN.md` clean
- [ ] `npx impeccable detect apps/web/src/` clean
- [ ] `/impeccable polish` run on every panel
- [ ] Replace any placeholder copy with real data
- [ ] Numbers formatted with thousands separators and two decimals (`USD 38,400.00`)
- [ ] Timestamps uniform (`08 May 13:00 LT`)
- [ ] No console errors, no console warnings
- [ ] Browser zoom set to 100%
- [ ] Browser at full screen on the demo laptop
- [ ] Wallpaper / dock cleaned up on the demo laptop
- [ ] One full demo run between rehearsals to confirm clean state
