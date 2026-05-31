# Laytimely docs — index and scoping rule

The hackathon is over. The ~30 planning docs that lived here have been
consolidated into **three documents, one per concern**. This index is the map;
the rule below is how we keep new docs from overlapping.

## The three buckets

| Doc | Bucket | Holds | Answers |
| --- | --- | --- | --- |
| [SYSTEM.md](SYSTEM.md) | **1 — System of Record** | everything that has been built | "what does Laytimely do / how is it built today?" |
| [ROADMAP.md](ROADMAP.md) | **2 — Roadmap** | planned, not-yet-built work | "what are we building next and why?" |
| [OPERATIONS.md](OPERATIONS.md) | **3 — Operations** | run locally, deploy the demo, migrate to AWS | "how do I run or ship it?" |

Two future product lines have full design depth, kept as bucket-2 detail docs
that ROADMAP points to (overview-altitude in ROADMAP, depth here — by design,
not overlap):

- [architecture_claims_radar.md](architecture_claims_radar.md) — live exposure detection.
- [architecture_emissions_compliance.md](architecture_emissions_compliance.md) — EU ETS / FuelEU.

## The scoping rule (so future docs do not overlap)

1. **Every doc belongs to exactly one bucket.** Before writing a new doc, decide
   which of the three it is. If it spans two, it is two edits to two existing
   docs, not one new doc.
2. **A feature is described in exactly one altitude per bucket.** SYSTEM.md
   describes built behaviour; ROADMAP describes intent; OPERATIONS describes
   running it. The same feature appears in more than one bucket only at each
   bucket's altitude, never duplicated.
3. **When something ships, it moves buckets.** Cut it from ROADMAP, add it to
   SYSTEM.md, and (if it changes how we run/deploy) update OPERATIONS.md. Do not
   leave a shipped feature described as "planned."
4. **Update, do not append.** Prefer editing the relevant doc over creating a
   new one. New standalone docs are only for genuine bucket-2 design depth
   (like the two architecture docs above), and they must be linked from
   ROADMAP.md.
5. **No em dashes; convert relative dates to absolute** when adding content.

## Provenance

The previous docs (00-PLAN through 22, `extended_plan`, `branch-state`, the
`production-*` briefs, `first_customer_checklist`, `frontend_revamp_plan`,
`landing_page_plan`, `product_roadmap`, `architecture_weeks_5_to_8`, and the
`new_features/` set) were the hackathon and post-hackathon planning trail. Their
content is captured in the three docs above and they were removed in the
2026-05-31 consolidation. Full history remains in git.
