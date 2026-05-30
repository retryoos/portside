# Frontend revamp plan — kill the AI slop, hit Revolut-grade

> The current frontend is functional but looks like every other 2025 AI-startup
> demo: WebGL gradient orbs behind frosted glass cards, restrained indigo accent,
> modest typography. Roman intended "glass" and shipped one of the AI-2025
> clichés. This plan replaces it with the editorial, photographic, confident
> language of the Revolut site (the screenshots in
> `apps/web/example_for_rebarnding/`, gitignored), driven by the `impeccable`
> Claude skill.
>
> Branch: `docs/first-customer-checklist` (same branch as the
> [first customer checklist](first_customer_checklist.md), since both are
> pre-customer prep doc work).
>
> The screenshots are gitignored, are not part of the deliverable, and will be
> deleted once the redesign lands.

---

## 1. Why the current frontend reads as AI slop

Audit of what is wrong, grounded in the actual code:

| Anti-pattern | Where it lives | Why it reads as slop |
| --- | --- | --- |
| WebGL gradient blob behind every page | [components/LiquidBackground.tsx](../apps/web/components/LiquidBackground.tsx) (328 lines) | The exact "AI-2025 hero shader" trope (Stripe demo / Anthropic / every YC company). It signals "this is a Claude wrapper" before the user reads a word. |
| Frosted glass cards over the shader | [components/ClaimScreen.tsx](../apps/web/components/ClaimScreen.tsx), [components/CaseHeader.tsx](../apps/web/components/CaseHeader.tsx) | Glass on top of gradient is the ChatGPT-clone signal. The cards have no opinion of their own. |
| Restrained indigo accent on near-white surfaces | [DESIGN.md](../apps/web/DESIGN.md) `--color-accent: oklch(0.55 0.17 268)` | Linear-clone palette. Calm and "trustworthy" but indistinguishable from every B2B SaaS. |
| Modest typography (15px body, 28px h1) | [DESIGN.md](../apps/web/DESIGN.md) typography block | Polite, not confident. Revolut hero is 60-100px, not 28. |
| Skeleton shimmer + crossfade reveal everywhere | PR 26 `<Reveal>` + globals.css shimmer | The skeleton-first trick is now a cliché. Reserved for it being *interesting* (a real pipeline), it currently reads as decorative. |
| No real photography, no brand mark in product chrome | TopNav wordmark only | Revolut puts a metallic 3D R in the body; we have a flat wordmark. |

The pieces individually are not wrong. The combination is the slop.

---

## 2. Visual direction shift

Distilled from the six Revolut screenshots:

| Dimension | Current (slop) | Target (Revolut-grade) |
| --- | --- | --- |
| Hero | Gradient orb shader | Full-bleed photographic plate + a tight glass card overlaid asymmetrically |
| Type scale | h1 28px, body 15px | h1 64-96px, body 16-18px. Confidence comes from size and tracking, not weight |
| Type voice | Sentence-case soft | Sentence-case but enormous, tight tracking (-0.04em), single-line where possible |
| Cards | Frosted glass over shader | Two kinds: solid white surfaces for body, true frosted-on-photo for hero overlays. No glass-on-gradient anywhere |
| Accent colour | Restrained indigo | Pure ink (#0A0A0A) + pure off-white pills with thick rounded corners. Indigo retired to focus rings and one chip state |
| Buttons | Pill outline / soft fill | Pure black pill or pure white pill on photographic ground. Stark and confident |
| Backgrounds | Animated orb everywhere | Mostly stark off-white (#FAFAFA) for content; reserved hero photographic moments |
| Motion | Continuous orb morph + skeleton shimmer | Restraint. One micro-animation per surface (the hero card slide-in). Nothing ambient. |
| Brand mark in chrome | Wordmark only | Compass mark + wordmark as a pair, with the compass scaled bold enough to register |

---

## 3. What dies, what stays, what gets reworked

### Dies (delete entirely)

- `LiquidBackground.tsx` (the WebGL shader). Removed from `app/layout.tsx`.
- `LiquidBackgroundFallback.tsx` (DOM-orb fallback).
- The shimmer utility class in `globals.css` for surfaces that already have real content (keep it only for the live pipeline stages, which are an *interesting* skeleton, not a decorative one).
- Any `backdrop-blur` on cards that sit on a solid surface (the blur is doing nothing there).

### Stays

- The OKLCH token system in `DESIGN.md` (the tokens are right; the *values* and the *typography scale* change).
- The component file structure (no rename storm).
- The `Reveal` crossfade on the live pipeline stages (genuinely useful there).
- The compass + wordmark pair in `TopNav.tsx` (already correct).

### Reworked

- DESIGN.md: new type scale, new palette values, new card spec, new motion principles. Section 4 below.
- Every page below: hero pattern, surface treatment, type rhythm. Section 5 below.

---

## 4. DESIGN.md revisions (per token group)

### 4.1 Typography (the biggest single lever)

| Token | Now | After |
| --- | --- | --- |
| `display` | 2.5rem (40px) | **5rem (80px) at desktop, 3rem (48px) at mobile**, weight 600, letter-spacing -0.04em |
| `h1` | 1.75rem (28px) | **3rem (48px) at desktop, 2rem at mobile**, weight 600, letter-spacing -0.03em |
| `h2` | 1.375rem | 2rem (32px), weight 600, letter-spacing -0.025em |
| `h3` | 1rem | 1.125rem (18px), weight 600 |
| `body` | 0.9375rem (15px) | **1rem (16px) baseline, 1.125rem (18px) on hero/marketing surfaces**, weight 400, line-height 1.6 |
| `body-sm` | 0.8125rem | 0.875rem (14px) |
| `eyebrow` (NEW) | — | 0.75rem, weight 600, letter-spacing 0.18em, uppercase |
| `letter-body` | unchanged | unchanged (the formal letter typography is correct as is) |

Rationale: the hero on slide 1 reads "Banking & Beyond" at ~80px. We currently read "Voyage cases" at 40px. That gap is the single biggest reason the product feels timid.

### 4.2 Palette

Retire indigo as the visible accent. Keep it only as the focus-ring colour. The visible accent becomes nothing: pure ink on off-white is the brand.

| Token | Now | After |
| --- | --- | --- |
| `primary` (ink) | oklch(0.23 0.006 265) | **oklch(0.15 0 0)** — purer black, cooler hue dropped |
| `neutral` (page bg) | oklch(0.981 0.002 265) | **oklch(0.985 0 0)** — pure off-white, no cool tint |
| `surface` (card bg) | oklch(0.997 0.001 265) | **oklch(1 0 0)** — true white cards on the off-white page so the edge is visible |
| `accent` | indigo oklch(0.55 0.17 268) | **same colour, used only for focus rings + one chip state**. Not on CTAs, not on links, not on dots. |
| `cta` (button bg) | ink | **pure ink, pure white text**, full pill radius. Same as Revolut Sign up. |
| `cta-inverse` (NEW) | — | white background, ink text, full pill. Same as Revolut Download the app. |

### 4.3 Surfaces and shadows

| Token | After |
| --- | --- |
| `radius-pill` (NEW) | `9999px` |
| `radius-card` | `1.25rem` (20px) — slightly tighter than current 24px |
| `radius-glass-card` (NEW) | `1.5rem` for hero-overlay glass only |
| `shadow-card` | tighten to a single `0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -16px rgba(0,0,0,0.08)` — closer to Revolut's barely-there shadow |
| `shadow-glass` (NEW) | `0 20px 80px -20px rgba(0,0,0,0.25)` — only for true glass-on-photo |

### 4.4 Motion principles (NEW section in DESIGN.md)

- No ambient motion. The shader is gone; nothing animates on idle.
- One micro-animation per surface, triggered by mount or by data arrival.
- Reveal stays only on the live pipeline.
- Hover transitions ≤ 150ms, ease-out.
- Reduced-motion media query disables everything but data-arrival reveals.

### 4.5 Photography (NEW section in DESIGN.md)

- Hero surfaces (login, marketing) get a full-bleed photo. Mood: maritime, port, calm. Subjects: ships at dock, port logistics, charterers reading documents. Not stock-ship-bow-cutting-water.
- Photo is the canvas; glass cards overlay it.
- Body surfaces (dashboard, case detail) do **not** carry photography. They are off-white.

---

## 5. Page and component revamp map

For each surface, the new pattern and the components affected.

### 5.1 `/login` — full-bleed photographic hero with glass card

New treatment:
- Full-viewport maritime photo (committed asset under `apps/web/public/login-hero.jpg`).
- A frosted glass card centred-right, holding the login form.
- "Papership.Ai" wordmark + compass on the card in pure white.
- "Welcome back" at 48px.
- One ink-on-white CTA pill: "Sign in".

Touches: [app/login/page.tsx](../apps/web/app/login/page.tsx), [app/login/LoginForm.tsx](../apps/web/app/login/LoginForm.tsx), DESIGN.md photography spec.

### 5.2 `/cases` — editorial dashboard, no shader

New treatment:
- Off-white page (no shader).
- Eyebrow "Demurrage" + headline "Voyage cases" at 80px above the table.
- "New voyage claim" as a pure ink pill, top right.
- Table: tighter row height, larger numeric column, status chips as solid pills (no glass).
- Empty state: a calm hero ("Three documents in, a claim out") with the CTA, no shader.

Touches: [app/cases/page.tsx](../apps/web/app/cases/page.tsx), [components/CasesTable.tsx](../apps/web/components/CasesTable.tsx), [components/Dropzone.tsx](../apps/web/components/Dropzone.tsx), [components/StatusBadge.tsx](../apps/web/components/StatusBadge.tsx), [components/StageChip.tsx](../apps/web/components/StageChip.tsx).

### 5.3 `/cases/[id]` — the claim, no shader

New treatment:
- Off-white page.
- Hero quantum **"EUR 84,375.00"** at 96px, weight 600, ink. Eyebrow above it: "Demurrage due to owners".
- Below the quantum: the formal letter on a true white card.
- Right rail: Sources / Calculation / Documents tabs as tight pills.
- AgentSteps stays as a labelled stepper, but on a solid surface.
- Reveal crossfade stays per-stage (this is the *interesting* skeleton).

Touches: [app/cases/\[id\]/page.tsx](../apps/web/app/cases/[id]/page.tsx), [components/ClaimScreen.tsx](../apps/web/components/ClaimScreen.tsx), [components/CaseHeader.tsx](../apps/web/components/CaseHeader.tsx), [components/ClaimLetter.tsx](../apps/web/components/ClaimLetter.tsx), [components/AgentSteps.tsx](../apps/web/components/AgentSteps.tsx), [components/SourcesTabs.tsx](../apps/web/components/SourcesTabs.tsx), [components/LaytimeSummary.tsx](../apps/web/components/LaytimeSummary.tsx), [components/SoFTable.tsx](../apps/web/components/SoFTable.tsx), [components/OutcomeTable.tsx](../apps/web/components/OutcomeTable.tsx).

### 5.4 `/vessels`, `/vessels/[name]` — same dashboard pattern

Mirror `/cases`. The fleet view gets the same editorial header at 80px.

Touches: [app/vessels/page.tsx](../apps/web/app/vessels/page.tsx), [app/vessels/\[name\]/page.tsx](../apps/web/app/vessels/[name]/page.tsx), [components/VesselsTable.tsx](../apps/web/components/VesselsTable.tsx).

### 5.5 `/revise` — keep, restyle

Inline revision UX stays. The surrounding chrome (page bg, header) shifts to off-white. The amber-tinted suggestion block becomes a true white card with a thin ink border (no tint).

Touches: [app/revise/page.tsx](../apps/web/app/revise/page.tsx), [components/ReviseActions.tsx](../apps/web/components/ReviseActions.tsx), [components/ReviseLetter.tsx](../apps/web/components/ReviseLetter.tsx), [components/RevisePrompt.tsx](../apps/web/components/RevisePrompt.tsx).

### 5.6 Global chrome

- `TopNav.tsx`: compass + wordmark scale up; nav links become subtle ink-on-off-white; account chip becomes a tight pill.
- `Reveal.tsx`: stays for pipeline stages, removed from every static surface.
- Root layout: `LiquidBackground` and its fallback removed; body bg becomes the new `neutral` token.

Touches: [components/TopNav.tsx](../apps/web/components/TopNav.tsx), [app/layout.tsx](../apps/web/app/layout.tsx), `globals.css`.

---

## 6. Subphased rollout (each one PR, mergeable independently)

Land in this order to keep the demo working at every step:

| # | PR title | What lands | Risk |
| --- | --- | --- | --- |
| **R0** | Revise DESIGN.md to the new tokens | DESIGN.md + the typography + palette + motion + photography sections. No code change. | None. |
| **R1** | Apply the new tokens in `theme.css` and `globals.css` | The OKLCH values and the new type scale flow through Tailwind. Visual shift everywhere, but each page still works. | Medium. Visual diff is large; review the whole app. |
| **R2** | Remove `LiquidBackground` + shimmer-on-static | Delete the shader, the fallback, the shimmer on non-pipeline surfaces. Root layout cleaned. | Low. The shader was decorative. |
| **R3** | Revamp `/login` to the photographic hero | New `login-hero.jpg` asset, new layout in `LoginForm.tsx`. | Low; isolated. |
| **R4** | Revamp `/cases` editorial header + table | Big hero type, off-white surface, restyled table + chips. | Medium. The dashboard is what investors see first. |
| **R5** | Revamp `/cases/[id]` quantum hero + letter card | 96px hero quantum, restyled letter card, restyled tabs, AgentSteps unchanged but on solid surface. | High. Most components touched. Use `impeccable` here. |
| **R6** | Revamp `/vessels` to mirror `/cases` | Mostly inheriting from R4. | Low. |
| **R7** | Restyle `/revise` to the new chrome | Inline revision palette + glass cleanup. | Low. |
| **R8** | TopNav scale-up + global chrome polish | Compass mark scales, nav simplification, account chip. | Low. |

R0 and R1 together change everything visually but break nothing. R2 onward is per-surface; the demo stays live throughout.

---

## 7. How to use the `impeccable` skill

Invoke `impeccable` at these moments:

1. **Before R0:** ask it to *audit* the screenshots and the current code, and produce the diff of design principles (Revolut vs current). Use the output to validate Section 2 of this plan.
2. **During R0:** ask it to *write* the new DESIGN.md, given the principles. Match the existing yaml-front-matter structure.
3. **During R1:** ask it to *translate* the new tokens into the OKLCH values in `apps/web/app/theme.css` and the type-scale classes in `globals.css`.
4. **During R5 (the high-risk one):** ask it to *redesign* the case-detail surface from the current screenshot + the new principles. Output should be a concrete component-tree diff, not prose.
5. **At the end of each PR:** ask it to *critique* the diff. Treat its critique as another reviewer.

Do not let `impeccable` run end-to-end on the whole app in one go. The risk is a single mega-PR that nobody can review. Use it per subphase.

---

## 8. Acceptance — how we know the slop is gone

- A blind viewer cannot identify the app as "an LLM wrapper" from a single screenshot of `/cases` or `/cases/<id>`.
- The hero on `/cases/<id>` reads at the same scale as the Revolut "Banking & Beyond" hero (proportionally to viewport).
- No animated background runs while the user is idle on any surface.
- The only places `backdrop-blur` appears are over a photograph.
- Pure indigo is visible nowhere on the dashboard except a focus ring.
- A reviewer asked "what does this remind you of?" answers Revolut, Apple, Linear, or "a serious product," not "Claude" or "ChatGPT" or "a startup demo."

---

## 9. Owner and timing

- **Owner:** whoever picks this up next (Roman is the natural owner; the `impeccable` skill makes the work tractable for any of us).
- **Timing:** R0 + R1 are half a day combined. R2 is an hour. R3-R8 are roughly half a day each. End to end, 3-4 days of focused work.
- **Branch policy:** each R-subphase is one PR off `main`. The plan itself lives on `docs/first-customer-checklist` because it is documentation work; the code revamp PRs branch off `main` independently.

---

## 10. Risk register

| Risk | Mitigation |
| --- | --- |
| The PDF export breaks on the new tokens (Tailwind v4 oklch crash, PR 26) | R1 must re-verify the export-time `oklch -> hex` scrub. Add a Playwright test that exports the demo letter and diffs the PDF for an unsupported color. |
| Investors prefer the old "AI demo" look | They will not. The Revolut language reads as confident, not naive. |
| Photography assets are not licensable | Buy from Unsplash / Pexels in advance, or commission a 1-day shoot at Piraeus. The login hero is the only mandatory photo. |
| The 96px hero quantum looks vulgar on a real claim ("EUR 1,247,832.50" overflows) | Add a numeric clamp: hero font-size scales down once the string passes 14 characters. Spec it in DESIGN.md typography. |
| Removing the shader makes the empty state feel cold | Replace with a one-line eyebrow + a quiet two-line headline. The Revolut "Your money's safe space" pattern proves stark works. |
