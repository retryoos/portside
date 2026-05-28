---
version: alpha
name: Portside
description: |
  A maritime demurrage claims tool for ship owners. The visual language is taken
  directly from the team mockups (notes reference: ../../mockup/screen_1..3.png):
  the gravitas of a barrister's opinion letter — serif headlines, warm paper,
  generous whitespace — with muted green for settled/positive outcomes, warm amber
  for warnings and contested time, and near-black ink for primary actions. Reads
  like a premium legal-tech product, not a SaaS dashboard.
colors:
  primary: "#1B1C18"
  on-primary: "#FAF9F6"
  secondary: "#6F6E66"
  neutral: "#FAF9F6"
  surface: "#FFFFFF"
  surface-muted: "#F3F1EB"
  border: "#E7E4DC"
  cta: "#1B1C18"
  on-cta: "#FFFFFF"
  cta-hover: "#33342D"
  accent: "#D98A2C"
  success: "#2F7A55"
  on-success: "#FFFFFF"
  success-container: "#E4F0E9"
  warning: "#A96A1E"
  on-warning: "#FFFFFF"
  warning-container: "#FBF1DC"
  contested: "#A96A1E"
  contested-container: "#FBF1DC"
  danger: "#B4453C"
  on-danger: "#FFFFFF"
  danger-container: "#F7E0DD"
typography:
  display:
    fontFamily: "Fraunces"
    fontSize: "2.5rem"
    fontWeight: 500
    letterSpacing: "-0.02em"
    lineHeight: 1.08
    fontVariation: "opsz 144"
  hero-figure:
    fontFamily: "Fraunces"
    fontSize: "2.5rem"
    fontWeight: 500
    letterSpacing: "-0.01em"
    lineHeight: 1.1
  h1:
    fontFamily: "Fraunces"
    fontSize: "1.75rem"
    fontWeight: 500
    lineHeight: 1.2
  h2:
    fontFamily: "Fraunces"
    fontSize: "1.375rem"
    fontWeight: 500
    lineHeight: 1.25
  h3:
    fontFamily: "IBM Plex Sans"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  letter-body:
    fontFamily: "Fraunces"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.7
  label-caps:
    fontFamily: "IBM Plex Sans"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.1em"
    lineHeight: 1.4
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  none: "0"
  sm: "4px"
  md: "8px"
  lg: "12px"
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
    padding: 24px
  button-primary:
    backgroundColor: "{colors.cta}"
    textColor: "{colors.on-cta}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
    typography: "{typography.body-sm}"
  button-primary-hover:
    backgroundColor: "{colors.cta-hover}"
    textColor: "{colors.on-cta}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
  timeline-item:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 20px
  timeline-item-settled:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 20px
  badge-success:
    backgroundColor: "{colors.success-container}"
    textColor: "{colors.success}"
    rounded: "{rounded.sm}"
    padding: "3px 9px"
  badge-warning:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    rounded: "{rounded.sm}"
    padding: "3px 9px"
  table-row-contested:
    backgroundColor: "{colors.contested-container}"
    textColor: "{colors.primary}"
    padding: "10px 16px"
  revise-highlight:
    backgroundColor: "{colors.contested-container}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 16px
---

## Overview

Portside is read by owners' claims executives and maritime lawyers. The mockups (`mockup/screen_1..3.png`) set the visual contract: **a barrister's opinion letter, not a SaaS dashboard.** Serif headlines (Fraunces), warm paper, lots of air. The product is calm and authoritative; colour is used sparingly and only to carry meaning — green for a won/settled outcome, amber for warning and contested time, ink for the one action you should take.

Style register: **product**, restrained and legal.

## Colors

- **`primary` `#1B1C18`** — warm near-black ink. All headings, body, table cells, and the primary CTA fill.
- **`secondary` `#6F6E66`** — warm gray. Metadata, captions, breadcrumbs, "27 May 2026" dates, section labels.
- **`neutral` `#FAF9F6`** — warm paper. Page background.
- **`surface` `#FFFFFF`** — cards, the letter sheet, timeline items.
- **`surface-muted` `#F3F1EB`** — secondary panels, the calculation summary block.
- **`border` `#E7E4DC`** — hairlines, card borders, table dividers.
- **`cta` `#1B1C18`** — the dark/ink buttons ("Send to charterer", "Accept"). White text. This replaces the old brass CTA — the mockups use ink buttons.
- **`accent` `#D98A2C`** — the warm amber dot beside a live case title. Decorative, used at most once per header.
- **`success` `#2F7A55` / container `#E4F0E9`** — settled, recovery rate, "Time bar cleared early", the settlement timeline item's left border.
- **`warning` `#A96A1E` / container `#FBF1DC`** — time-bar countdown warnings.
- **`contested` `#A96A1E` / container `#FBF1DC`** — contested SoF rows AND the inline-revise highlight block. Same warm amber.
- **`danger` `#B4453C` / container `#F7E0DD`** — the strikethrough on text the agent replaced during a revision; reject actions.

All foreground/background pairs meet WCAG AA.

## Typography

- **Fraunces (serif)** — `display`, `h1`, `h2`, AND `hero-figure` (the big "Demurrage due to owners: USD 84,375.00" is **serif, not mono** — this is the single biggest type correction from the mockups), AND `letter-body` (the formal claim letter is set in Fraunces, like a printed legal letter).
- **IBM Plex Sans** — `body`, `body-sm`, `h3`, `label-caps`. The UI chrome, nav, metadata, section labels ("DISPUTE TIMELINE", "TO: CHARTERERS").
- **JetBrains Mono** — `mono`, tabular. Used **only** inside the Statement-of-Facts calculation table (TIMESTAMP / CUM. HRS columns) and other dense numeric tables where vertical alignment matters. NOT for the hero figure.

`label-caps` (small, tracked, uppercase, secondary color) marks every section: "DISPUTE TIMELINE", "OUTCOME", "TO: CHARTERERS", "SOURCES / CALCULATION / DOCUMENTS" tabs.

Web fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

## Layout

- Page background warm paper; content sits on white cards with hairline borders, **no drop shadow**.
- **Top app bar** with the serif "Portside" wordmark + nav: Dashboard · Claims · Vessels · Reports, and search / notifications / settings / profile icons on the right (screen 1).
- **Breadcrumb row** under the bar: "Vessels / MT Aegean Pioneer / Settled" or "Voyages / MT Aegean Pioneer".
- Generous max-width content column (~720–960px), centered, not full-bleed — this is what gives the editorial feel.
- The claim view (screen 2) is **two columns**: the letter (left, ~58%) and the Sources/Calculation/Documents panel (right, ~42%).

## Elevation & Depth

No drop shadows, no glows. Depth comes from the warm-paper-vs-white contrast and hairline borders. The one sanctioned accent stripe: a 3px **green** left border on a settlement/positive timeline item, and a left border on the inline-revise highlight block.

## Shapes

Rounded corners: `sm` (4px) on buttons/badges/table accents, `md` (8px) on cards and timeline items. Nothing fully pill-shaped except the small status badges. Documents have near-square corners.

## Components

- **`button-primary`** — ink fill, white text. "Send to charterer", "Accept", "Send rebuttal". Sparingly: one primary action per view.
- **`button-ghost`** — text-only secondary actions ("View full letter →", "Export full case file (PDF)", "Reject").
- **`timeline-item`** — a white card in the dispute correspondence timeline (screen 1). Date in `secondary` on the left, actor + summary on the right. The "Detected from inbox" badge marks auto-assembled correspondence.
- **`timeline-item-settled`** — same, with the 3px green left border + a green check, for the settlement-accepted row.
- **`badge-success` / `badge-warning`** — small status chips (recovery rate, "Cleared 67 days early"; time-bar countdown).
- **`table-row-contested`** — amber-tinted SoF row (the disputed stoppage).
- **`revise-highlight`** — the amber block that holds the agent's replacement text during inline revision (screen 3), paired with `danger` strikethrough on the text being replaced.

## Confidence display

Show owner position strength as a word — **Strong / Arguable / Weak** — never a numeric percentage. Senior arbitrators read numeric confidence as gimmicky.

## Screens (the three mockups — authoritative reference)

These supersede the old three-panel layout in [notes/06-frontend.md](../../notes/06-frontend.md) wherever they differ. 06-frontend's *content* (laytime table, quantum, dispute narrative, letter) still applies — it just maps onto these layouts.

1. **Case detail / settled** (`screen_1.png`) — top nav + breadcrumb + serif title ("MT Aegean Pioneer — Ras Tanura / Rotterdam", "Settled at USD 79,000 — 21 days from claim submission") + a vertical **dispute correspondence timeline** (claim submitted → charterer response *"Detected from inbox"* → rebuttal sent → revised offer → settlement accepted) + an **Outcome** table (original claim, settled at, recovery %, days to settlement, time-bar status "Cleared 67 days early").
2. **Claim view** (`screen_2.png`) — breadcrumb + amber time-bar countdown + ink "Send to charterer". Two columns: the **formal letter** (left, "TO: CHARTERERS", serif hero figure "Demurrage due to owners: USD 84,375.00", letter body) and a right panel with **Sources / Calculation / Documents** tabs showing the laytime summary block + the **SoF timeline table** (TIMESTAMP / DESCRIPTION / CATEGORY / CUM. HRS, contested row amber).
3. **Inline highlight-and-revise** (`screen_3.png`) — full-width letter; a floating quick-prompt ("Make the weather argument stronger and cite The Mexico 1"); the old sentence struck through in `danger`; the replacement paragraph in a `revise-highlight` amber block (citing The Mexico 1 [1990] 1 Lloyd's Rep 507 + Rotterdam Port Authority precipitation data); an **Accept / Reject** control. See [notes/13-inline-revision.md](../../notes/13-inline-revision.md).

## Demo content (align to the mockups)

Use the mockup voyage, not the old Piraeus one: **MT Aegean Pioneer, Ras Tanura → Rotterdam**, CP dated 12 Feb 2026, demurrage USD 45,000/day, laytime 72h allowed / 117h used, **claim USD 84,375.00**, contested 4-hour weather stoppage on 17 May, weather clause on a **precipitation threshold (0.5 mm/hr)**, authority **The Mexico 1 [1990] 1 Lloyd's Rep 507**. Rotterdam keeps us consistent with the "Europe, starting in Greece" positioning.

## Do's and Don'ts

### Do
- Tint every neutral (ink is `#1B1C18`, gray is `#6F6E66`, never pure `#000`/`#808080`).
- Set the hero demurrage figure and the letter body in **Fraunces serif**.
- Use mono **only** in the SoF calculation table.
- One ink primary button per view; everything else is ghost/text.
- Use green only for won/settled/positive, amber only for warning/contested/revise.
- Right-align numeric table columns.

### Don't
- Don't use Inter or a generic geometric sans.
- Don't use the old burnished-brass CTA — CTAs are ink now.
- Don't set the hero figure in monospace.
- Don't add drop shadows, gradients, or nested cards.
- Don't show numeric confidence percentages.
- Don't use more than the three accent colours (green, amber, the single warm dot).
