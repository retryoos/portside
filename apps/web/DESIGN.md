---
version: 1.0
name: Papership.Ai
register: product
description: |
  A maritime demurrage and laytime resolution tool for ship owners and the
  lawyers who handle their claims. The visual language is editorial and
  confident: bold sentence-case headlines at the scale of a magazine cover,
  generous off-white surfaces, true frosted-glass cards reserved for hero
  surfaces over photography, stark pill CTAs in pure ink or pure white. No
  ambient motion, no gradient orbs, no decorative shimmer. Inter throughout,
  weight 600 for confidence, tight tracking on large sizes. The aesthetic
  reference is the Revolut consumer site: photography for hero moments,
  stark white for body, ruthless restraint on colour. Pure indigo is retired
  from visible surfaces and survives only as the focus ring.
colors:
  primary: "oklch(0.15 0 0)"
  on-primary: "oklch(0.99 0 0)"
  secondary: "oklch(0.46 0.005 265)"
  neutral: "oklch(0.985 0 0)"
  surface: "oklch(1 0 0)"
  surface-muted: "oklch(0.965 0.003 265)"
  border: "oklch(0.91 0.004 265)"
  border-strong: "oklch(0.82 0.005 265)"
  cta: "oklch(0.15 0 0)"
  on-cta: "oklch(0.99 0 0)"
  cta-hover: "oklch(0.28 0 0)"
  cta-inverse: "oklch(1 0 0)"
  on-cta-inverse: "oklch(0.15 0 0)"
  cta-inverse-hover: "oklch(0.93 0.003 265)"
  accent: "oklch(0.55 0.17 268)"
  accent-container: "oklch(0.95 0.03 268)"
  success: "oklch(0.5 0.12 155)"
  on-success: "oklch(0.99 0.01 155)"
  success-container: "oklch(0.94 0.04 155)"
  warning: "oklch(0.55 0.13 70)"
  on-warning: "oklch(0.99 0.01 70)"
  warning-container: "oklch(0.94 0.05 75)"
  contested: "oklch(0.55 0.13 70)"
  contested-container: "oklch(0.94 0.05 75)"
  danger: "oklch(0.52 0.18 25)"
  on-danger: "oklch(0.99 0.01 25)"
  danger-container: "oklch(0.94 0.045 25)"
  glass-tint: "oklch(1 0 0 / 0.55)"
  glass-tint-strong: "oklch(1 0 0 / 0.78)"
  glass-stroke: "oklch(1 0 0 / 0.32)"
typography:
  hero:
    fontFamily: "Inter"
    fontSize: "5rem"
    fontSizeMobile: "3rem"
    fontWeight: 600
    letterSpacing: "-0.04em"
    lineHeight: 1.0
  hero-figure:
    fontFamily: "Inter"
    fontSize: "6rem"
    fontSizeMobile: "3.5rem"
    fontWeight: 600
    letterSpacing: "-0.045em"
    lineHeight: 1.0
  display:
    fontFamily: "Inter"
    fontSize: "3.5rem"
    fontSizeMobile: "2.25rem"
    fontWeight: 600
    letterSpacing: "-0.035em"
    lineHeight: 1.05
  h1:
    fontFamily: "Inter"
    fontSize: "2.5rem"
    fontSizeMobile: "1.75rem"
    fontWeight: 600
    letterSpacing: "-0.03em"
    lineHeight: 1.1
  h2:
    fontFamily: "Inter"
    fontSize: "1.75rem"
    fontWeight: 600
    letterSpacing: "-0.02em"
    lineHeight: 1.2
  h3:
    fontFamily: "Inter"
    fontSize: "1.125rem"
    fontWeight: 600
    letterSpacing: "-0.01em"
    lineHeight: 1.35
  body:
    fontFamily: "Inter"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  body-lg:
    fontFamily: "Inter"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "Inter"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  letter-body:
    fontFamily: "Inter"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.75
  eyebrow:
    fontFamily: "Inter"
    fontSize: "0.75rem"
    fontWeight: 600
    letterSpacing: "0.18em"
    lineHeight: 1.2
    textTransform: "uppercase"
  label-caps:
    fontFamily: "Inter"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.14em"
    lineHeight: 1.4
    textTransform: "uppercase"
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  none: "0"
  sm: "8px"
  md: "12px"
  card: "20px"
  glass: "24px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "64px"
  3xl: "96px"
shadows:
  card: "0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -16px rgba(0,0,0,0.08)"
  glass: "0 24px 80px -24px rgba(0,0,0,0.28)"
  focus-ring: "0 0 0 3px oklch(0.55 0.17 268 / 0.35)"
motion:
  ease-out: "cubic-bezier(0.2, 0.7, 0.1, 1)"
  duration-fast: "120ms"
  duration-base: "180ms"
  duration-slow: "320ms"
photography:
  hero:
    treatment: "Full-bleed colour photography, port and maritime subjects."
    crop: "1.6:1 minimum at desktop, 1:1 acceptable at mobile."
    glassOverlay: "true"
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.card}"
    padding: 32px
    border: "1px solid {colors.border}"
    shadow: "{shadows.card}"
  card-muted:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
    rounded: "{rounded.card}"
    padding: 24px
  card-glass:
    backgroundColor: "{colors.glass-tint-strong}"
    textColor: "{colors.primary}"
    rounded: "{rounded.glass}"
    padding: 32px
    border: "1px solid {colors.glass-stroke}"
    backdropFilter: "blur(24px) saturate(140%)"
    shadow: "{shadows.glass}"
  button-primary:
    backgroundColor: "{colors.cta}"
    textColor: "{colors.on-cta}"
    rounded: "{rounded.pill}"
    padding: "12px 22px"
    typography: "{typography.body-sm}"
    fontWeight: 600
  button-primary-hover:
    backgroundColor: "{colors.cta-hover}"
    textColor: "{colors.on-cta}"
  button-inverse:
    backgroundColor: "{colors.cta-inverse}"
    textColor: "{colors.on-cta-inverse}"
    rounded: "{rounded.pill}"
    padding: "12px 22px"
    typography: "{typography.body-sm}"
    fontWeight: 600
  button-inverse-hover:
    backgroundColor: "{colors.cta-inverse-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    border: "1px solid {colors.border-strong}"
    rounded: "{rounded.pill}"
    padding: "12px 20px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.pill}"
    padding: "10px 16px"
  nav-pill:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  nav-pill-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
  chip:
    rounded: "{rounded.pill}"
    padding: "4px 12px"
    typography: "{typography.label-caps}"
    border: "1px solid {colors.border}"
  table-row-contested:
    backgroundColor: "{colors.contested-container}"
    textColor: "{colors.primary}"
    padding: "12px 16px"
---

## Overview

Papership.Ai is the demurrage workspace for ship owners and the lawyers who
file their claims. The product is read on monitors in claims rooms and on
laptops in port-agent offices; the surface needs to feel quiet, confident,
and worth a six-figure decision.

The visual register is **product editorial**: massive sentence-case headlines,
generous off-white surfaces, photography for the hero moments that ask the
viewer to stop, and a single ink-on-off-white CTA palette that does not need
colour to read as confident. The aesthetic reference is the Revolut consumer
site: hero photography overlaid with a tight frosted-glass card, body sections
on stark white, pure black or pure white pill buttons, and ruthless restraint
on accent colour.

Indigo is retired from visible surfaces. It survives only as the focus-ring
colour. Every primary CTA is ink-on-off-white or its inverse.

There is **no ambient motion** in the app. The decorative WebGL shader that
sat behind every page is gone, the shimmer that ran on every card is gone,
and the soft-light orbs are gone. The only animation in the product is the
crossfade reveal of pipeline stages as their data arrives, which is
*interesting* skeleton, not decorative.

Style register: **product editorial**, confident and quiet.

> **Pivot note.** This document supersedes the ElevenLabs-derived
> "clean-product palette" that preceded it. Roman's prior implementation of
> glass-on-shader read as 2025 AI-startup boilerplate; the revamp plan in
> [`notes/frontend_revamp_plan.md`](../../notes/frontend_revamp_plan.md)
> records the diagnosis. The token shifts here are the floor of that revamp.

## Colours

Tokens are OKLCH. The neutral set is **un-tinted** (no faint cool hue): pure
off-white for the page, pure white for cards, near-black for the ink. The
single visible chromatic moment in the product is the indigo focus-ring.

- **`primary`** (ink): #1A1A1A-equivalent near-black. Headings, body, table
  cells, the primary CTA fill.
- **`secondary`**: muted gray. Metadata, captions, eyebrow labels.
- **`neutral`**: stark off-white. Page background everywhere except hero
  surfaces.
- **`surface`**: pure white. Cards, the letter sheet, tab panels. The edge
  reads against `neutral` because the page is off-white.
- **`surface-muted`**: very faint gray. Secondary panels, table headers.
- **`border`** / **`border-strong`**: hairlines. Used sparingly; depth comes
  from fill contrast, not borders.
- **`cta`** / **`on-cta`**: ink pill on white text. Used once per view.
- **`cta-inverse`** / **`on-cta-inverse`**: white pill, ink text. Used over
  photography or over the ink hero surface only.
- **`accent`**: indigo. **Focus rings only.** Not visible on a CTA, not a
  link colour, not a dot.
- **`success`** / **`warning`** / **`contested`** / **`danger`**: semantic
  status for the claim lifecycle, otherwise unused. Container variants for
  background fills.
- **`glass-tint`** / **`glass-tint-strong`** / **`glass-stroke`**: the only
  place we use translucent white. Reserved for cards that sit over
  photography. Never over a solid surface.

All foreground/background pairs meet WCAG AA.

## Typography

Inter, weights 400 and 600. Hierarchy comes from scale and tracking, not
weight. The display range is large by design: confidence reads as size on
the big surfaces and as restraint on the body.

- **`hero`** (5rem desktop, 3rem mobile, 600, -0.04em): the dashboard and
  vessel page headline ("Voyage cases"). Editorial scale.
- **`hero-figure`** (6rem desktop, 3.5rem mobile, 600, -0.045em): the
  demurrage quantum on case detail ("EUR 84,375.00"). The single largest
  thing in the product.
- **`display`** (3.5rem, 600, -0.035em): the login welcome and other
  intermediate marquee headlines.
- **`h1`** (2.5rem, 600, -0.03em): card and section titles inside a page.
- **`h2`** / **`h3`** as a measured ladder.
- **`body`** (1rem, 400): the new baseline (up from 0.9375rem).
- **`body-lg`** (1.125rem, 400): hero body copy and marketing context.
- **`letter-body`** (1rem, 400, line-height 1.75): the formal claim letter.
- **`eyebrow`** (0.75rem, 600, 0.18em tracked, uppercase): the small
  category label above every hero.
- **`label-caps`** (0.6875rem, 600, 0.14em): table column heads, tab pills.
- **`mono`**: numeric column in the SoF table only.

Web fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

### Hero figure clamping

The 6rem hero quantum looks magisterial on `EUR 84,375.00` (12 chars including
spacing). A real claim string can be longer (`EUR 1,247,832.50` is 17 chars).
Apply a clamp: once the rendered string passes 14 characters, fall back to the
5rem display size. Implement via a CSS class on the figure, not a JS measure.

## Layout

- Page background **stark off-white** (`neutral`); content sits on pure-white
  `surface` cards with a hairline border and almost no shadow. Depth is fill
  contrast and radius.
- **Top app bar**: compass mark + wordmark on the left, nav pills in the
  middle, account chip on the right. Pills are 16px-padded.
- Content column max-width **1100px** for dashboard surfaces, **1240px** for
  the case detail (which has the wider letter + right rail).
- Hero surfaces fill more vertical space than they did before. The dashboard
  hero is at least 240px tall before the table starts; the case detail hero
  is at least 320px tall before the letter card.

## Photography

Hero surfaces use real photography. Mood: maritime, port, calm. Subjects:
ships at dock, port logistics, charterers reading documents in good light.
Avoid stock photo cliches (ship bow cutting water, drone shots of containers
in pure geometric grids).

- Crop: 1.6:1 minimum at desktop, 1:1 minimum at mobile.
- The photograph is the canvas. A `card-glass` overlay sits asymmetrically
  on top, holding the headline and CTA.
- Body surfaces (dashboard rows, case detail letter, tabs) do **not** carry
  photography. They are off-white.
- Local assets under `apps/web/public/photography/`. Names: `hero-login.jpg`,
  `hero-empty.jpg`, etc. JPEG, ~85% quality, ≤200 KB after compression.

If a photo is not yet committed, fall back to a deep-ink solid surface with
the same headline. Do **not** fall back to a gradient.

## Motion

Motion principles, in order:

1. **No ambient motion.** Nothing animates while the user is idle. No drifting
   orbs, no shimmer, no pulsing dots.
2. **One micro-interaction per surface.** Hover and focus transitions are
   `120ms` ease-out. CTAs lift 1px on hover, no more.
3. **Data-arrival reveal only.** The crossfade on pipeline stages stays;
   nothing else gets one.
4. **Reduced motion:** the media query disables every transition that lasts
   more than 100ms and removes every transform.

## Elevation and depth

- `shadows.card`: barely-there single-layer shadow (`0 1px 2px / 0 8px 24px -16px`).
  Used on white cards over off-white pages, sparingly.
- `shadows.glass`: the only "dramatic" shadow in the system, used on
  `card-glass` over photography.
- `shadows.focus-ring`: a 3px indigo halo at 35% alpha. The only place
  indigo appears.
- **No drop shadows on chips, buttons, table rows, or inputs.**

## Shapes

- Pills (`pill`) on buttons, nav tabs, chips, badges.
- `card` (20px) on white surface cards.
- `glass` (24px) on `card-glass`.
- `sm` (8px) on inputs and small icon buttons.

## Components

- **`button-primary`**: ink pill, white text, 600 weight, 22px horizontal
  padding. One per view.
- **`button-inverse`**: white pill, ink text. Used over photography or over a
  dark hero. Never on a white card.
- **`button-secondary`**: transparent with `border-strong` outline. Used for
  the second action.
- **`button-ghost`**: text-only pill in secondary colour. Tertiary actions.
- **`nav-pill`**: pill nav item; active state is `primary` fill, `on-primary`
  text. No grey-on-grey middle ground.
- **`card`** / **`card-muted`**: white or very-faint-grey rounded panels.
- **`card-glass`**: the frosted overlay for hero photography only. Backdrop
  blur 24px, saturate 140%, `glass-stroke` hairline, `shadows.glass`.
- **`chip`**: small pill status chip with hairline border. No coloured fill
  unless the chip carries a semantic meaning (settled, contested, rejected).
- **`table-row-contested`**: amber-tinted SoF row, full tint, no left stripe.
- **No `backdrop-filter` outside `card-glass`.**
- **No decorative gradients anywhere.** The previous `gradient-warm` /
  `gradient-cool` orbs are removed.

## Confidence display

Show owner position strength as a word: **Strong / Arguable / Weak**, never a
numeric percentage. Senior arbitrators read numeric confidence as gimmicky.

## Surfaces (the live app routes)

1. **Login** (`/login`): full-bleed maritime hero photograph, `card-glass`
   overlaid centre-right holding the wordmark, "Welcome back" at `display`
   scale, and the form. One ink-on-white `button-primary` "Sign in".
2. **Dashboard** (`/cases`): off-white page. `eyebrow` label
   "DEMURRAGE WORKSPACE", `hero` headline "Voyage cases", a short body line,
   a `button-primary` "New voyage claim" top-right. Below: the cases table on
   a white card, empty state on a quiet panel, no shader.
3. **Case detail** (`/cases/<id>`): off-white page. `eyebrow` label
   "DEMURRAGE DUE TO OWNERS", `hero-figure` quantum "EUR 84,375.00", below it
   the formal letter on a white card, right rail with Sources / Calculation /
   Documents tabs (label-caps on pills). AgentSteps stays as the labelled
   stepper but on a solid surface; the per-stage Reveal crossfade is the
   only animation.
4. **Vessels** (`/vessels`, `/vessels/<name>`): same pattern as `/cases`.
5. **Inline revise** (`/revise`): full-width letter card, the floating
   quick-prompt as a `card-glass` on the page, the replaced sentence struck
   through in `danger`, the suggestion in a white card with a hairline
   border, Accept / Reject.

## Demo content

**MT Aegean Pioneer, Ras Tanura / Rotterdam**, CP dated 12 Feb 2026, demurrage
EUR 45,000/day, laytime 72h allowed / 117h used, **claim EUR 84,375.00**,
contested 4-hour weather stoppage on 17 May, weather clause on a precipitation
threshold (0.5 mm/hr), authority **The Mexico 1 [1990] 1 Lloyd's Rep 507**.
Money stays `EUR 84,375.00`; timestamps stay `17 May 14:00 LT`.

## Do's and Don'ts

### Do
- Use the new `hero` / `hero-figure` sizes on the marquee surfaces. They are
  the entire reason this revamp exists.
- Carry the whole UI in Inter; reserve mono for the SoF table.
- Use pills for buttons, tabs, chips. Use 20-24px rounding on cards.
- One ink primary button per view. Pair it with `button-secondary` ghost or
  outline if needed; never two filled buttons.
- Use green only for settled, amber only for contested or time-bar warning,
  red for rejected. No other colour.
- Right-align numeric table columns.
- Use the indigo accent only for focus rings.

### Don't
- Don't bring back the WebGL shader, the soft-light orbs, or any animated
  background. They were the slop signal.
- Don't apply `backdrop-filter` to anything that is not `card-glass` over
  a photograph.
- Don't bring back Fraunces or set the hero figure / letter in serif.
- Don't add drop shadows to chips, buttons, table rows, or table cells.
- Don't use gradient text (`background-clip: text`) or nested cards.
- Don't use side-stripe coloured borders; use full background tints.
- Don't use decorative status dots; use labeled steppers and chips.
- Don't show numeric confidence percentages.
- Don't use em dashes in UI copy or content; use commas, colons, or hyphens.
- Don't introduce a new colour token without retiring an existing one.
