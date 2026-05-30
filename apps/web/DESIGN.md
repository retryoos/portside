---
version: beta
name: Papership.Ai
register: product
description: |
  A maritime demurrage claims tool for ship owners. The visual language is taken
  from the team mockups in "../../mockup to design like/" (ElevenLabs / ElevenCreative
  product screens): clean and near-monochrome, a single well-tuned geometric sans,
  generous whitespace, large-radius soft cards, pill-shaped buttons and tabs, and
  colour held back to decorative gradient orbs plus a restrained semantic set for
  claim status. Calm, modern, trustworthy product UI, not a busy dashboard.
colors:
  primary: "oklch(0.23 0.006 265)"
  on-primary: "oklch(0.985 0.002 265)"
  secondary: "oklch(0.556 0.008 265)"
  neutral: "oklch(0.981 0.002 265)"
  surface: "oklch(0.997 0.001 265)"
  surface-muted: "oklch(0.966 0.003 265)"
  border: "oklch(0.922 0.004 265)"
  cta: "oklch(0.23 0.006 265)"
  on-cta: "oklch(0.985 0.002 265)"
  cta-hover: "oklch(0.32 0.006 265)"
  accent: "oklch(0.55 0.17 268)"
  accent-container: "oklch(0.95 0.03 268)"
  success: "oklch(0.55 0.11 155)"
  on-success: "oklch(0.99 0.01 155)"
  success-container: "oklch(0.95 0.03 155)"
  warning: "oklch(0.58 0.11 70)"
  on-warning: "oklch(0.99 0.01 70)"
  warning-container: "oklch(0.95 0.045 75)"
  contested: "oklch(0.58 0.11 70)"
  contested-container: "oklch(0.95 0.045 75)"
  danger: "oklch(0.55 0.17 25)"
  on-danger: "oklch(0.99 0.01 25)"
  danger-container: "oklch(0.94 0.035 25)"
typography:
  display:
    fontFamily: "Inter"
    fontSize: "2.5rem"
    fontWeight: 600
    letterSpacing: "-0.025em"
    lineHeight: 1.05
  hero-figure:
    fontFamily: "Inter"
    fontSize: "2.5rem"
    fontWeight: 600
    letterSpacing: "-0.025em"
    lineHeight: 1.1
  h1:
    fontFamily: "Inter"
    fontSize: "1.75rem"
    fontWeight: 600
    letterSpacing: "-0.02em"
    lineHeight: 1.2
  h2:
    fontFamily: "Inter"
    fontSize: "1.375rem"
    fontWeight: 600
    letterSpacing: "-0.015em"
    lineHeight: 1.25
  h3:
    fontFamily: "Inter"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Inter"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Inter"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  letter-body:
    fontFamily: "Inter"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.75
  label-caps:
    fontFamily: "Inter"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.08em"
    lineHeight: 1.4
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  none: "0"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "64px"
gradients:
  warm: "linear-gradient(135deg, oklch(0.84 0.12 70), oklch(0.72 0.16 25), oklch(0.63 0.16 305))"
  cool: "linear-gradient(135deg, oklch(0.8 0.12 250), oklch(0.82 0.09 200), oklch(0.84 0.1 150))"
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: 24px
  card-soft:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: 20px
  button-primary:
    backgroundColor: "{colors.cta}"
    textColor: "{colors.on-cta}"
    rounded: "{rounded.full}"
    padding: "10px 20px"
    typography: "{typography.body-sm}"
  button-primary-hover:
    backgroundColor: "{colors.cta-hover}"
    textColor: "{colors.on-cta}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    border: "{colors.border}"
    rounded: "{rounded.full}"
    padding: "10px 18px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.full}"
    padding: "10px 16px"
  nav-tab:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.full}"
    padding: "6px 14px"
  nav-tab-active:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
  badge:
    rounded: "{rounded.full}"
    padding: "3px 10px"
    typography: "{typography.label-caps}"
  table-row-contested:
    backgroundColor: "{colors.contested-container}"
    textColor: "{colors.primary}"
    padding: "10px 16px"
---

## Overview

Papership.Ai is read by owners' claims executives and maritime lawyers. The mockups in
[`../../mockup to design like/`](../../mockup%20to%20design%20like/) set the visual
contract: an ElevenLabs-style product surface. Clean, near-monochrome, a single
geometric sans (Inter), lots of air, large-radius soft cards, and pill chrome.
Colour is held back: decorative gradient orbs carry visual interest, while a small
semantic set (green / amber / red) carries claim status only. The product feels
calm, modern, and trustworthy. The tool disappears into the task.

Style register: **product**, clean and modern.

> **Pivot note (this is a deliberate departure).** Earlier Papership.Ai used a
> Fraunces serif / warm-paper "barrister's letter" identity. The team mockups are
> ElevenLabs product screens, and the direction is to adopt that aesthetic in full,
> so the serif/warm-paper identity is retired. The hero quantum and claim letter
> are now Inter, not serif. Where this document and the mockups once conflicted on
> serif vs sans or warm vs cool, the mockups win.

## Colors

Tokens are OKLCH and tinted toward a faint cool hue (~265). Never `#000` / `#fff`.

- **`primary`**: ink near-black. Headings, body, table cells, primary CTA fill.
- **`secondary`**: muted gray. Metadata, captions, breadcrumbs, section labels.
- **`neutral`**: soft cool white. Page background.
- **`surface`**: white cards, the letter sheet, tab panels.
- **`surface-muted`**: soft gray cards and secondary panels (the calculation block,
  the inactive sources cards). This is the dominant "soft card" fill, ElevenLabs-style.
- **`border`**: hairlines, card borders, table dividers.
- **`cta` / `cta-hover`**: the ink pill buttons. White text. One primary per view.
- **`accent`**: a single restrained indigo. Links, focus rings, at most one small
  status marker. Not decoration.
- **`success` / container**: settled, recovery, positive time-bar status.
- **`warning` / `contested` / containers**: time-bar countdown and contested SoF time.
- **`danger` / container**: rejected claims, struck text in revision.

All foreground/background pairs meet WCAG AA.

## Typography

- **Inter** carries everything: `display`, `hero-figure`, `h1`, `h2`, `h3`, `body`,
  `body-sm`, `letter-body`, and `label-caps`. Hierarchy comes from scale + weight
  (600 for headings/figures, 400 for body), with tightened tracking on large sizes.
- **JetBrains Mono** is used **only** in the Statement-of-Facts calculation table
  (TIMESTAMP / CUM. HRS columns) where vertical numeric alignment matters.
- `label-caps` (small, tracked, uppercase, secondary) marks every section:
  "DISPUTE TIMELINE", "OUTCOME", "TO: CHARTERERS", and the Sources / Calculation /
  Documents tabs.

Web fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

## Layout

- Page background soft cool white; content sits on white or soft-gray cards with
  hairline borders or no border, **no drop shadow**. Depth is fill contrast + radius.
- **Top app bar** with the "Papership.Ai" wordmark + pill nav tabs (Claims, Vessels),
  active tab a soft-gray pill. Primary actions on the right are pills.
- **Breadcrumb row** under the bar.
- Generous max-width content column (720–1200px), centered, not full-bleed.
- The claim view is **two columns**: the letter (left, ~58%) and the
  Sources/Calculation/Documents panel (right, ~42%).

## Elevation & Depth

No drop shadows, no glows. Depth comes from the soft-gray-vs-white fill contrast and
hairline borders. **No side-stripe accents** (no `border-left` colour bars): contested
and positive states use full background tints, not coloured left borders.

## Shapes

Generous rounding. Pills (`full`) on buttons, nav tabs, chips, and badges.
`lg` (16px) / `xl` (24px) on cards and panels. `sm` (8px) on inputs and small accents.

## Components

- **`button-primary`**: ink pill, white text. "Send to charterer", "Accept". One per view.
- **`button-secondary`**: white pill with hairline border. Secondary actions.
- **`button-ghost`**: text-only pill, secondary colour. Tertiary actions, "Export".
- **`nav-tab`**: pill nav item; active is a soft-gray pill.
- **`card` / `card-soft`**: white (hairline) or soft-gray (no border) rounded panels.
- **`badge`**: small pill status chip (claim stage, time bar, recovery).
- **`table-row-contested`**: amber-tinted SoF row (full tint, no left stripe).
- **gradient orbs**: `gradients.warm` / `gradients.cool` decorative media on the
  dashboard hero and empty states. Never used behind text via `background-clip: text`.

## Confidence display

Show owner position strength as a word: **Strong / Arguable / Weak**, never a numeric
percentage. Senior arbitrators read numeric confidence as gimmicky.

## Surfaces

The live app routes (these are what ship):

1. **Dashboard** (`/cases`): voyage cases table, claim-stage chips, a gradient hero
   strip, the "New voyage claim" pill revealing the upload dropzone, empty + loading states.
2. **Case detail** (`/cases/<id>`): the formal claim letter (left), Inter hero quantum
   ("Demurrage due to owners: EUR 84,375.00"), and a right panel with Sources /
   Calculation / Documents tabs (laytime summary + SoF table, contested row amber).
   Lifecycle actions: Send to charterer -> settled | rejected -> revise & resend.
   A labeled numbered stepper shows live pipeline progress (no pulsing dots).
3. **Vessels** (`/vessels`, `/vessels/<name>`): fleet aggregate view, reusing the
   cases table and chips.
4. **Inline revise** (`/revise`): full-width letter with a floating quick-prompt; the
   replaced sentence struck through in `danger`, the suggestion in an amber-tinted
   block (full tint, no left stripe), Accept / Reject.

## Demo content (align to the mockups)

**MT Aegean Pioneer, Ras Tanura / Rotterdam**, CP dated 12 Feb 2026, demurrage
EUR 45,000/day, laytime 72h allowed / 117h used, **claim EUR 84,375.00**, contested
4-hour weather stoppage on 17 May, weather clause on a precipitation threshold
(0.5 mm/hr), authority **The Mexico 1 [1990] 1 Lloyd's Rep 507**. Money stays
`EUR 84,375.00`; timestamps stay `17 May 14:00 LT`.

## Do's and Don'ts

### Do
- Tint every neutral toward the cool hue; never pure `#000` / `#fff`.
- Carry the whole UI in Inter; reserve mono for the SoF table.
- Use pills for buttons, tabs, chips; large radius for cards.
- One ink primary button per view; everything else is secondary/ghost.
- Use green only for settled/positive, amber only for warning/contested, red for rejected.
- Right-align numeric table columns.

### Don't
- Don't bring back Fraunces or set the hero figure / letter in serif.
- Don't add drop shadows, gradient text (`background-clip: text`), or nested cards.
- Don't use side-stripe coloured borders; use full background tints.
- Don't use decorative status dots; use labeled steppers and chips.
- Don't show numeric confidence percentages.
- Don't use em dashes in UI copy or content; use commas, colons, or hyphens.
