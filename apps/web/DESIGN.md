---
version: alpha
name: Portside
description: |
  A maritime claims tool. The product is read by claims executives, charterers,
  and maritime lawyers — readers who spend their day inside contracts. The visual
  language borrows from that world: the gravitas of a counsel's letterhead with
  the data-density of a Bloomberg terminal. Serif for authority, monospace for
  numbers, a warm-paper background that reads like the file folder this work has
  always lived in.
colors:
  primary: "#0A1929"
  on-primary: "#F8F6F1"
  secondary: "#475569"
  tertiary: "#9C5A2F"
  on-tertiary: "#FFFFFF"
  tertiary-container: "#7E4624"
  neutral: "#F8F6F1"
  surface: "#FFFFFF"
  surface-muted: "#F1EEE7"
  border: "#D9D4C8"
  success: "#15803D"
  on-success: "#FFFFFF"
  success-container: "#DCFCE7"
  warning: "#B45309"
  on-warning: "#FFFFFF"
  warning-container: "#FED7AA"
  danger: "#B91C1C"
  on-danger: "#FFFFFF"
  danger-container: "#FECACA"
  contested: "#D97706"
  contested-container: "#FEF3C7"
typography:
  display:
    fontFamily: "Fraunces"
    fontSize: "4rem"
    fontWeight: 500
    letterSpacing: "-0.02em"
    lineHeight: 1.05
    fontVariation: "opsz 144"
  h1:
    fontFamily: "Fraunces"
    fontSize: "2rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  h2:
    fontFamily: "Fraunces"
    fontSize: "1.5rem"
    fontWeight: 500
    lineHeight: 1.25
  h3:
    fontFamily: "IBM Plex Sans"
    fontSize: "1.0625rem"
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.08em"
    lineHeight: 1.4
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  mono-quantum:
    fontFamily: "JetBrains Mono"
    fontSize: "3.75rem"
    fontWeight: 500
    letterSpacing: "-0.02em"
    lineHeight: 1
rounded:
  none: "0"
  sm: "2px"
  md: "4px"
  lg: "6px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "64px"
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  card-muted:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
    typography: "{typography.label-caps}"
  button-primary-hover:
    backgroundColor: "{colors.tertiary-container}"
    textColor: "{colors.on-tertiary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  table-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    padding: "12px 16px"
  table-row-contested:
    backgroundColor: "{colors.contested-container}"
    textColor: "{colors.primary}"
    padding: "12px 16px"
  table-row-demurrage:
    backgroundColor: "{colors.danger-container}"
    textColor: "{colors.primary}"
    padding: "12px 16px"
  badge-timebar-ok:
    backgroundColor: "{colors.success-container}"
    textColor: "{colors.success}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  badge-timebar-warning:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  badge-timebar-danger:
    backgroundColor: "{colors.danger-container}"
    textColor: "{colors.danger}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
---

## Overview

Portside is read by people who spend their day inside contracts. The interface should feel like the file folder this work has always lived in — but loaded with the speed and clarity of a trading terminal. Two motifs:

- **Letterhead gravitas.** Serif for headings (Fraunces) reads like the top of a formal claim letter. Warm-paper background (`#F8F6F1`) reads like the file you opened on your desk. No floating accents, no gradients, no whitespace-for-whitespace's-sake.
- **Data-room precision.** Monospace numbers (JetBrains Mono) for every timestamp and dollar figure — they need to align vertically across rows, and they need to read instantly. The headline quantum is set in a very large monospace because that is the number the user is here for.

Style register: **product**, not brand. We are an instrument, not a campaign.

## Colors

The palette is rooted in **deep marine ink** on **warm paper**, with **burnished brass** as the only call-to-action accent. Tinted neutrals throughout — no pure black, no pure gray.

- **`primary` `#0A1929`** — Deep marine ink. Headings, body text, table cells. Reads as authoritative without being literal navy.
- **`secondary` `#475569`** — Tinted slate. Captions, metadata, "from / to" labels, supporting copy.
- **`tertiary` `#9C5A2F`** — Burnished brass. Reserved for the primary call-to-action (`Generate Claim Letter`, `New Voyage Claim`). Used sparingly; the eye should find it instantly because there is no competition for it.
- **`neutral` `#F8F6F1`** — Warm paper background. Page-level fill.
- **`surface` `#FFFFFF`** — Pure white, only inside cards where the data demands maximum clarity (the laytime table, the letter preview).
- **`surface-muted` `#F1EEE7`** — Slightly darker paper. For the left panel's document cards, to set them off from the main canvas without using shadow.
- **`border` `#D9D4C8`** — A warm-tinted line one shade above paper. Use for hairlines, table dividers, card borders.
- **Status colors:**
  - `success` `#15803D` + `success-container` `#DCFCE7` — time-bar > 30 days
  - `warning` `#B45309` + `warning-container` `#FED7AA` — time-bar 1–30 days
  - `danger` `#B91C1C` + `danger-container` `#FECACA` — time-bar passed; "on demurrage" rows
  - `contested` `#D97706` + `contested-container` `#FEF3C7` — flagged laytime rows

All foreground/background pairs in the `components` block exceed WCAG AA 4.5:1.

## Typography

The type system has three voices, each with a job:

- **Fraunces (serif)** — display + h1 + h2. Variable opsz axis tuned to display at the largest sizes. This is the voice of "this is a formal document." It does not appear in body, buttons, or labels.
- **IBM Plex Sans** — body + label-caps + h3. The chosen sans is deliberately *not* Inter, *not* a generic geometric sans. IBM Plex has a slightly mechanical, drafted-with-precision character that fits the maritime/industrial subject.
- **JetBrains Mono** — every number, every timestamp, every dollar amount. Fixed width is non-negotiable for the laytime table. The `mono-quantum` token is the headline number at the bottom of the center panel; the size is deliberately oversized to make it the gravitational center of the screen.

`label-caps` (small, tracked, uppercase) is used for table headers, the "DOCUMENTS | LAYTIME TIMELINE | CLAIM PACKET" panel labels, and button text. It contributes to the "data-room" feel without shouting.

Web font loading:

```html
<!-- in app/layout.tsx -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

## Layout

- Page-level: warm paper background (`{colors.neutral}`), full-bleed.
- Three-panel layout: 25% / 45% / 30% on `lg:` and up. Single-column tab switcher below `md:`.
- Cards: subtle border (`{colors.border}`), no shadow. Shadow on hairlines feels SaaS-template.
- Hairlines between table rows; no zebra striping.
- Gap between panels: `{spacing.lg}` (24px). Gap inside cards: `{spacing.md}` (16px).

## Elevation & Depth

Portside has **no elevation system**. No drop shadows, no glows, no card stacking. Depth comes from color tinting (paper vs. surface vs. surface-muted), not from shadow. This is the deliberate visual contract: "we are not a SaaS template."

The single exception: the contested-row inline expansion has a 1px left border in `{colors.contested}` to mark its boundary. That is the only depth cue in the product.

## Shapes

Rounded corners are restrained. `rounded.sm` (2px) on buttons. `rounded.md` (4px) on cards. Nothing larger. Pills, bubbles, and circles do not appear. The product looks like a document — documents have square corners.

## Components

The `components` block in front-matter defines tokens. Below is rationale.

- **`card`** — the document cards (left panel) and the right-panel content blocks. White surface, border, no shadow.
- **`card-muted`** — the document cards when *not* the focus. Reads as "passive evidence" — there, available, but not asking for attention.
- **`button-primary`** — burnished brass. Reserved for the two CTAs in the product: **New Voyage Claim** and **Generate Claim Letter**. Do not use brass anywhere else. If a third button feels like it needs to be primary, the screen has too many primaries.
- **`button-secondary`** — surface with border. Used for `Download PDF`, `Download Word`, `View Excerpt`.
- **`table-row-contested`** — warm amber tint. Used for the flagged laytime rows that drive the demo.
- **`table-row-demurrage`** — soft red tint. Used for rows where the vessel is on demurrage.
- **`badge-timebar-*`** — the top-bar countdown chip. The single most credible UX detail in the product.

## Do's and Don'ts

### Do

- Tint every neutral. Black is `{colors.primary}` (#0A1929), not `#000000`. Gray is `{colors.secondary}` (#475569), not `#808080`.
- Right-align every number column. The eye lines up dollars and timestamps vertically; left-aligned numbers are unreadable in a maritime context.
- Set every monetary value with two decimals and thousands separators: `USD 38,400.00`.
- Set every timestamp in port-local time with the suffix `LT`: `08 May 13:00 LT`.
- Use `label-caps` for panel titles and column headers — short, tracked, uppercase.
- Keep the brass accent rare. One per screen, ideally one per viewport.

### Don't

- Don't use Inter. The product is not a SaaS template.
- Don't use gray text on a colored background; readability dies and contrast usually fails.
- Don't use pure black or pure gray. Always tint.
- Don't wrap cards inside cards. The left-panel document cards live directly on the warm paper, no parent card.
- Don't use bounce / elastic / spring easing. The product is formal. Use linear or ease-out for everything; reserve motion for state changes only.
- Don't use gradients. None. The product reads as a printed document, and printed documents do not gradient.
- Don't use purple, teal, or any unearned accent color. The palette has one accent (brass). Adding a second weakens the first.
- Don't use circular avatars, decorative icons, or status dots for anything informational. The status chip carries the status; a redundant dot is just SaaS reflex.
- Don't animate on scroll. Don't animate on hover (except a subtle color shift on buttons). Motion is a state-change tool, not a decoration tool.
