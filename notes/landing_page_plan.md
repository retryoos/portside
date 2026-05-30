# Landing page plan — Papership.Ai marketing front

> A production-grade marketing site that sits in front of the product, in the
> same editorial Revolut-grade language we just shipped for the app. It is
> the first thing any prospect, investor, journalist, or shipping ops manager
> sees, and it is the surface that converts a curious read into a signed
> account.
>
> Built in the same direction as the just-landed
> [`frontend_revamp_plan.md`](frontend_revamp_plan.md): massive sentence-case
> headlines, full-bleed photography, true frosted-glass overlays, stark pill
> CTAs, no ambient motion, no gradient orbs.
>
> Branch: same as the rest of the docs (`docs/first-customer-checklist`).

---

## 1. Goal and framing

The landing page does three jobs, in this order:

1. **Convert a cold reader** into someone who wants the product. The hero must
   make a shipping ops manager pause inside the first 1.5 seconds.
2. **Showcase the product** with real product surfaces, not vague marketing
   illustrations. The Revolut site works because the product is on screen the
   moment you scroll; ours has to do the same.
3. **Be the line of defence in front of the app.** Unauthenticated users see
   the landing page; the product lives behind the login. This means a single
   policy at the routing layer, not in components.

It is **not** a feature page wall, a doc site, or a content marketing blog.
It is a long single-page product showcase with a discreet footer that holds
the legal pages.

---

## 2. Architecture decision

Three viable shapes for where the landing lives. Recommendation: **option B**,
ship in the same Next.js app under a clear routing split.

### Option A — Separate Next.js project, separate Vercel deploy

- `landing/` next to `apps/web/`, deployed to `papership.ai`.
- App lives at `app.papership.ai`.

Pros: clean separation, marketing iterations cannot break the app, can be
maintained by a marketing person without touching app code.
Cons: two repos to keep in design sync, two Vercel projects, two CI pipelines,
shared design tokens become a published package or are duplicated.

### Option B — Same Next.js app, route split (recommended)

- Landing lives in `apps/web/app/(marketing)/` route group.
- Product lives in `apps/web/app/(app)/` route group.
- The middleware in `apps/web/middleware.ts` decides which surface a request
  hits and gates the app group behind auth.

Pros: single source of truth for design tokens, single deploy, single
analytics. Marketing iterations carry the same Inter + token system the
product already uses. Editorial code reviews catch drift.
Cons: marketing and app share `next build` time and bundle. Mitigated by
Next.js route groups: marketing pages stay static-only and do not pull in the
product's client code.

### Option C — Subdomain rewrite via Vercel

- `papership.ai` and `app.papership.ai` are both served from one Vercel
  project via wildcard, with edge rewrites by host.
- Code stays in one repo.

Pros and cons sit between A and B. This is the natural migration path **if**
the same-app split outgrows itself, e.g. when the marketing site adds a CMS
and the build time gets uncomfortable.

### Decision rule

Start with B. Move to C only when one of these is true: marketing iterations
are blocked by app review, marketing wants a CMS (Sanity, Contentlayer) the
app does not need, or the marketing team grows past one person.

---

## 3. Information architecture

The landing is a long-form single page with anchor sections, plus a small set
of meta pages reachable only from the footer.

### Single-page sections (in scroll order)

1. **Hero** — full-bleed photograph, headline, one-line subheadline, primary
   CTA, secondary CTA.
2. **Problem** — three short sentences on the manual reality, set in big
   editorial type on stark white.
3. **Product showcase** — looped, captioned screen recordings of the three
   beats: upload, watch the four agents land, the finished claim with
   citations. This is the spine of the page.
4. **How it works** — the four-agent pipeline as a diagram, with one short
   line on what each agent owns.
5. **Trust and provenance** — citation chain, deterministic arithmetic,
   audit-ready PDF export, time-bar protection.
6. **Quotes / logos** — placeholders for design partner quotes and logos. Hidden
   on first launch; revealed when real ones land.
7. **Pricing** — three-tier card row (self-serve, partner, enterprise).
   Numbers as placeholders, revealed in Tier 1.
8. **CTA strip** — second-chance ask: book a demo or start a trial.
9. **Footer** — wordmark, sitemap, legal links, social, address.

### Meta pages (footer-only, indexable)

- `/security` — what we encrypt, how we authenticate, how data leaves the
  account.
- `/privacy` — privacy policy.
- `/terms` — terms of service.
- `/contact` — sales address, support email, claims-team email.
- `/changelog` — public changelog (optional, post-launch).

### What it does NOT have

- A blog. Blogs are debt unless someone is paid to write weekly.
- A docs site. Until a real customer asks, in-product help is enough.
- An interactive sandbox. The demo voyage inside the app is the sandbox.

---

## 4. Visual direction (carried over)

The landing inherits every token in
[`apps/web/DESIGN.md`](../apps/web/DESIGN.md). No new colour, no new font.
The only new construct is a **section** primitive that turns scroll into
rhythm.

Direction recap:

- **Type scale already exists.** `text-hero` (5rem desktop) for marquee
  headlines, `text-display` (3.5rem) for intermediate, `text-h1` (2.5rem) for
  section heads, `text-body-lg` for hero copy, `text-body` for body.
- **Photography carries hero surfaces.** A photo bleeds full-width, a
  `card-glass` sits over it asymmetrically.
- **Body sections are stark off-white** (`bg-neutral`) with massive type and
  generous space.
- **Pills only.** `bg-cta` ink-on-white pill on neutral; `bg-cta-inverse`
  white-on-ink pill on photography or the inverse hero.
- **Indigo is the focus ring** and nothing else.
- **No ambient motion.** Section reveals on scroll are the only non-CTA
  motion, and they are 250ms ease-out, single direction, never looping.

---

## 5. Routing and the line-of-defence policy

The whole point of "in front of the product" is that the unauthenticated user
never sees the app. This is a one-rule middleware change, not a UI change.

### Current state

`apps/web/middleware.ts` gates every route except `/login` and `/api/auth/*`
to require a session cookie. `/` redirects to `/cases` via the dashboard.

### Target state

- The marketing route group (`/`, `/security`, `/privacy`, `/terms`,
  `/contact`) is **public**.
- The app route group (`/cases`, `/cases/[id]`, `/vessels`, `/vessels/[name]`,
  `/revise`) is **gated**: missing or invalid session → 302 to
  `/login?next=<original>`.
- `/login` and `/api/auth/*` remain public.
- `/` no longer redirects; it renders the marketing hero.

### Implementation

```ts
// apps/web/middleware.ts
const APP_PREFIXES = ["/cases", "/vessels", "/revise"];
const PUBLIC_EXACT = new Set(["/", "/login", "/security", "/privacy", "/terms", "/contact"]);

export function middleware(req) {
  const { pathname } = new URL(req.url);
  if (pathname.startsWith("/api/auth/")) return NextResponse.next();
  if (PUBLIC_EXACT.has(pathname)) return NextResponse.next();
  if (APP_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return requireSession(req); // existing helper
  }
  // Default deny: anything new is gated until the matcher is updated.
  return requireSession(req);
}
```

The matcher in the middleware config excludes `_next/static`, images,
favicon, the photography directory, and the API auth routes.

---

## 6. Component primitives (new)

All under `apps/web/components/marketing/`. Each one is single-purpose, no
prop drilling.

| Component | Responsibility | Sits on |
| --- | --- | --- |
| `MarketingNav.tsx` | Top-of-page nav: compass + wordmark + Pricing + Contact + Sign in pill. Fixed but transparent over the hero; solidifies into `bg-neutral/85` once scrolled past the hero. | every marketing route |
| `Container.tsx` | Max-width 1240px, lateral padding tokens. The only horizontal container in the marketing build. | every section |
| `Section.tsx` | Vertical rhythm primitive: `py-24 md:py-32` plus a `Container`. Variants: `bg-neutral` (default), `bg-primary` (inverse), `bg-photo` (full-bleed hero). | every section |
| `Eyebrow.tsx` | The `text-eyebrow` label every section opens with. | reusable across sections |
| `Hero.tsx` | The first viewport: photograph, glass card, headline, body, two CTAs. | `/` only |
| `ScrollReveal.tsx` | A wrapper that fades and 8-pixel translates a child into view on first intersection. Disabled under `prefers-reduced-motion`. | sections 2-8 |
| `CTASection.tsx` | The reusable "second-chance" CTA strip. | bottom of `/` |
| `Footer.tsx` | Wordmark + sitemap + legal + social. Off-white surface, no shader. | every marketing route |
| `LoopVideo.tsx` | `<video autoplay muted loop playsinline>` with a poster image and a manual play/pause control for reduced motion. Captures the product-tour beats. | section 3 of `/` |
| `PipelineDiagram.tsx` | The four-agent flow rendered as four labelled cards with hairline connectors between them. SVG, accessible, scaled. | section 4 of `/` |

These are the only new components needed. Everything else (CTA pills, type
classes, focus rings) is the existing system.

---

## 7. Page-by-page spec

### 7.1 `/` — the long-form landing

**Above the fold (Hero):**

- Full-bleed photograph at `public/photography/hero-landing.jpg` (port at
  dawn, tanker discharging, calm).
- Diagonal ink scrim for legibility.
- `MarketingNav` transparent.
- Left two-thirds: eyebrow "Maritime claims, automated.", text-hero headline
  "Recover the demurrage you're owed." or
  "Three documents in. A finished claim out.", text-body-lg subline, two
  pills: primary ink "Book a demo", inverse "See the product".
- Right one-third: empty or holds a small floating quote card.

**Section 2 — Problem:**

- `bg-neutral` section.
- Eyebrow "Today".
- Three sentence headline in `text-display`:
  > "A ship waits too long. The owner is owed money. Claiming it takes days,
  > by hand."
- Three short body paragraphs in `text-body-lg`, one each on documents,
  specialists, expiring claims.

**Section 3 — Product showcase:**

- `bg-primary` (inverse) section so the product surfaces stand out.
- Eyebrow "How it looks".
- Section headline "Three documents in. A finished claim out. In under a
  minute."
- Three vertically stacked `LoopVideo` clips with captions:
  - Upload: drag-and-drop the three PDFs, watch the cases-table row appear.
  - Process: the four-agent stepper running, then the case-detail hero
    landing with the EUR 84,375.00 quantum.
  - Edit + export: highlight a sentence, refine it with AI, export the PDF.

**Section 4 — How it works:**

- `bg-neutral`.
- Eyebrow "Under the hood".
- Section headline "Four agents. One pipeline. Every figure cited."
- `PipelineDiagram`: Read → Calculate → Argue → Draft, each card has one
  line on what the agent owns and one line on the trust property (the
  calculator note: "math runs in plain code").

**Section 5 — Trust and provenance:**

- `bg-neutral`.
- Eyebrow "Trust".
- Three short trust statements, each a small white card with hairline
  border:
  - Every figure traces to its source line.
  - The arithmetic is deterministic Python, not the model.
  - The 90-day time-bar is tracked per claim.

**Section 6 — Quotes (deferred):**

- Hidden on first launch. Empty state of "Quotes from design partners
  coming soon" looks worse than no section. Add when real ones land.

**Section 7 — Pricing:**

- `bg-neutral`.
- Eyebrow "Pricing".
- Three pricing cards in a row, equal-height. Tiers: self-serve, partner,
  enterprise. Each card: tier name, one-line audience, three feature
  bullets, ink-pill CTA. Numbers placeholder until Tier 1.

**Section 8 — CTA strip:**

- `bg-primary` section.
- Section headline "Stop losing valid claims to deadlines you missed."
- Two pills: primary inverse "Book a demo", secondary inverse outline
  "Read the docs".

**Footer:**

- Compass + wordmark, four columns (Product, Company, Legal, Get in touch),
  social icons row, copyright line.

### 7.2 `/security`

A single editorial column page. Sections: identity (Cognito), data at rest
(encrypted RDS + S3), data in transit (TLS), access control, audit logging,
the response plan, the contact email. Text-led, no photography, no glass.

### 7.3 `/privacy`, `/terms`

Plain editorial columns. Long. Boring on purpose. The only design rule is
the `text-display` page title plus eyebrow.

### 7.4 `/contact`

Two cards: sales email and support email. A simple email signup for
"engineering updates" if we want a list, otherwise drop it.

---

## 8. Performance and SEO

### Performance budget

| Metric | Target | Notes |
| --- | --- | --- |
| Largest Contentful Paint | < 2.0s | The hero photograph drives this. Pre-load it. |
| First Contentful Paint | < 1.0s | Inline critical CSS for the hero. |
| Cumulative Layout Shift | < 0.05 | Photograph and font swap are the only risks. |
| Total Blocking Time | < 200ms | Marketing pages must not import the product client bundle. |
| Page weight | < 1.2 MB transferred at LCP | Hero photo budget: 280 KB AVIF. |

### Asset pipeline

- Photography under `apps/web/public/photography/`. Source: an editorial
  shoot or licensed stock at minimum 2880px wide.
- Pipeline: AVIF + WebP + JPEG fallback via `next/image`. Quality 78,
  responsive sizes 480 / 960 / 1440 / 1920 / 2560.
- Loop videos under `apps/web/public/showcase/`. Format: MP4 H.264 + WebM
  VP9. Looped at 1280×720, ~2-3 MB per clip after compression. `preload="metadata"`,
  `playsinline`, `muted`, `loop`.

### SEO

- `app/(marketing)/layout.tsx` carries default Open Graph + Twitter card
  metadata; per-page overrides.
- Structured data (`schema.org/Organization`, `WebSite`, `Product`) inlined
  in the root marketing layout.
- `sitemap.ts` exposes the marketing routes; the app routes are blocked in
  `robots.ts`.
- Canonical URLs on every page.
- One H1 per page, the `text-hero` headline.

---

## 9. Analytics and conversion

- **Vercel Web Analytics** (free) for traffic. Privacy-friendly, no cookie,
  no consent banner needed in the EU.
- **Plausible** for a richer view if we want it later; same drop-in.
- **Event tracking on the four CTAs that matter:**
  `hero_book_demo`, `hero_see_product`, `cta_strip_book_demo`,
  `pricing_select_<tier>`.
- A simple `analytics.ts` wrapper so the underlying provider can swap
  without touching the components.

No third-party analytics that drops a cookie. No Google Analytics, no
LinkedIn Insight Tag in MVP. Add them only after we have a paid customer.

---

## 10. Subphased rollout (one PR each, mergeable independently)

| # | PR title | What lands | Risk |
| --- | --- | --- | --- |
| **L0** | Routing split: marketing + app route groups | `(marketing)/` and `(app)/` route groups, middleware policy update, `/` no longer redirects. Marketing routes are placeholder pages. | Medium. Auth gate must stay tight. |
| **L1** | Marketing primitives: `MarketingNav`, `Container`, `Section`, `Eyebrow`, `Footer` | Reusable building blocks for the rest of L2 onward. | Low. |
| **L2** | Hero section + the landing photograph | The first viewport of `/`. Asset pipeline integrated. | Medium. Photography asset is on the critical path. |
| **L3** | Problem and How-it-works sections (text-only) | Sections 2 and 4 of `/`. | Low. |
| **L4** | Product showcase loops (section 3) | The three `LoopVideo` clips. Captured from the live demo voyage. | High. Requires production-quality screen capture; this is the single most decisive section. |
| **L5** | Trust + Pricing + CTA strip (sections 5, 7, 8) | The rest of the long-form page. | Low. |
| **L6** | Footer + meta pages (`/security`, `/privacy`, `/terms`, `/contact`) | The legal floor. Text-led. | Low. |
| **L7** | Performance pass: image optimisation, font loading, critical CSS | Web Vitals all green. | Medium. The hero photo dominates the budget. |
| **L8** | SEO: metadata, structured data, sitemap, robots | Indexability and rich previews. | Low. |
| **L9** | Analytics + conversion tracking | Vercel Analytics + the four CTA events. | Low. |

L0 → L2 are blocking. L3 → L9 can be parallelised once primitives exist.

---

## 11. How to use the `impeccable` skill

1. **Before L1:** ask it to audit the existing
   [`apps/web/DESIGN.md`](../apps/web/DESIGN.md) plus the Revolut reference
   screenshots and produce a short doc on the gaps between "product editorial"
   (what the app needs) and "marketing editorial" (what the landing needs).
   The differences are real and small: marketing tolerates one extra rhythm
   primitive (`Section`) and one extra typographic rule (alternating ink and
   neutral grounds).
2. **During L2:** ask it to redesign the hero from the screenshots and the
   problem statement. Output is a component tree plus CSS, not prose.
3. **During L4:** ask it to direct the three showcase clips. What to capture,
   in what order, at what speed, with what captions. The clips are the most
   decisive part of the page.
4. **During L7:** ask it to critique the Lighthouse trace. Treat it as a
   second reviewer.

Same rule as the app revamp: do not let it run end-to-end on the whole
marketing site. One subphase at a time.

---

## 12. Acceptance criteria

- A returning visitor on a cold cache reaches LCP in under 2 seconds on a
  4G connection, measured via PageSpeed Insights.
- An anonymous visitor cannot reach `/cases`, `/cases/<id>`, `/vessels`,
  `/vessels/<name>`, or `/revise`; they are 302'd to `/login?next=`.
- Hitting `/` while signed in still shows the marketing page. The
  product is **not** auto-loaded; the user clicks "Open the app" in the
  nav to switch.
- A keyboard-only user can navigate the entire landing, including the
  showcase loops (focus-visible ring on every CTA, video controls reachable).
- Reduced-motion users see no looped video and no scroll reveals; clips
  show their poster image with a play button.
- The Open Graph preview on LinkedIn, Twitter, and Slack is the hero photo
  with the headline overlaid.
- A reviewer asked "what does this remind you of?" answers Revolut, Stripe,
  or Linear, not "another AI startup."

---

## 13. Risk register

| Risk | Mitigation |
| --- | --- |
| The hero photograph is generic stock and reads as fake | Commission a 1-day port shoot at Piraeus or licence a single distinctive frame from a known marine photographer. Either is < EUR 1,000. |
| The product showcase clips look like a screen recording, not a product moment | Treat L4 like a design phase, not a capture phase. Storyboard before recording, capture at 60 fps, edit with consistent cursor speed, add 6-px focus rings on the click moments. |
| Pricing numbers leak before we're ready | Hide section 7 behind a feature flag until the numbers are signed off. |
| The middleware route policy ships with a hole | Make the default policy "deny" and the public allowlist explicit. Add a Playwright test that hits each protected route unauthenticated and asserts the 302. |
| The marketing bundle pulls in `react-markdown` or `html2pdf.js` from the app | Use Next.js route groups, then audit the marketing route's First Load JS in the `next build` output; alert if it crosses 120 kB. |
| LCP regresses when a real photograph lands | Pre-load the hero photo, set `priority` on the `next/image`, and run a manual Lighthouse trace in CI before merging L7. |
| The auth swap to Cognito (Tier 1 of the customer checklist) breaks marketing routes | Keep auth logic in a single helper (`requireSession`) so the Cognito swap touches one file, not the middleware policy. |

---

## 14. Owner and timing

- **Owner:** Roman (continuation of the app revamp), or whoever picks up
  from the [hand-off prompt](../notes/first_customer_checklist.md). The
  `impeccable` skill makes the work tractable for anyone.
- **Timing:**
  - L0 + L1: half a day combined.
  - L2: half a day of code, plus the photograph procurement on a separate
    track.
  - L3 + L5 + L6: one day combined.
  - L4: one full day (this is the decisive section; do not rush it).
  - L7 + L8 + L9: one day combined.
- **End to end: ~4 working days** of focused work, plus the photo and
  showcase clip procurement on a parallel track.
- **Branch policy:** L0 through L9 each as one PR off `main`. The plan
  itself lives on `docs/first-customer-checklist` because it is
  documentation work; the marketing build PRs are independent.

---

## 15. What is deliberately NOT in this plan

- A CMS. We do not have enough marketing content to justify it yet.
- Internationalisation. English-only at launch. Greek follows once we
  have a Greek customer.
- A blog. See Section 3.
- A status page. The product has no public uptime SLA yet.
- Affiliate or referral programs. Premature.
- Marketing automation (Mailchimp, HubSpot). One email per quarter from a
  founder beats a drip campaign at this stage.
