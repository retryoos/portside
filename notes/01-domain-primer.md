# Domain Primer — Laytime, Demurrage, and the Vocabulary of a Port Call

> Read this before you write a prompt or build a UI panel. Every label, every column, every agent output uses this vocabulary. Getting one term wrong in the demo is a tell to the judge that we are tourists.

---

## 1. The core economic event

A shipowner chartered a vessel to a charterer for a voyage. They agreed:
- The vessel would arrive at the port and be made available for cargo operations.
- The charterer has a contractually agreed amount of time — **laytime** — to load (and/or discharge) without paying extra.
- If the charterer takes longer than laytime, they owe **demurrage** (a per-day penalty, pre-agreed in the charter party).
- If they finish before laytime expires, the owner owes **despatch** (a reward, usually half the demurrage rate).

The fight: how much time was actually used, and which time counts.

## 2. Key documents

### Charter Party (CP)
The contract between owner and charterer. Different standard forms for different trades:
- **ASBATANKVOY** — tanker voyage charter (used in oil trades; what we will demo)
- **GENCON** — BIMCO general purpose dry cargo voyage charter
- **NYPE 93** — time charter (not us, but you will see references)
- **Shellvoy** — Shell tanker voyage form
- **BPVOY** — BP tanker voyage form

The CP contains the laytime allowed (e.g., "72 hours SHINC"), the demurrage rate ("USD 30,000 per day pro rata"), the despatch rate ("half demurrage on all working time saved"), the loading and discharging port(s), the laycan window, and the exception clauses.

### Notice of Readiness (NOR)
A formal notice from the master to the charterer (or shipper/receiver) that the vessel has arrived and is **ready in all respects** to load or discharge. Tendering NOR triggers the clock — laytime usually starts a fixed number of hours after NOR is tendered (e.g., "6 hours after tender of NOR or commencement of cargo operations, whichever is earlier").

For NOR to be valid:
- Vessel must be at the agreed location (the port, the berth, or the customary anchorage)
- Vessel must be physically and legally ready (cargo holds clean, tanks ready, free pratique granted, customs cleared)
- NOR must be tendered during the hours/days specified in the CP (e.g., "0600–1800 local time on any day except Sunday")

### Statement of Facts (SoF)
A chronological record of every event at the port. Each row has a timestamp, an event description, and (often) a category. Signed by the master, the port agent, and frequently the receiver/shipper.

Typical SoF events:
- Arrived at pilot station
- Pilot on board
- Anchored
- NOR tendered
- NOR accepted
- Inward clearance / free pratique granted
- All fast at berth (vessel moored)
- Hoses connected (tanker) / hatches opened (dry cargo)
- Commenced loading / discharging
- Stoppage — rain
- Stoppage — equipment breakdown
- Stoppage — shift change
- Resumed loading / discharging
- Completed loading / discharging
- Hoses disconnected / hatches closed
- Documents on board
- Departed berth

Every stoppage is a potential dispute.

## 3. Laytime exception clauses (memorise these)

These letter combinations are the live wires. They tell the calculator which time counts.

| Abbreviation | Meaning                                               | Effect on laytime                                                                       |
| ------------ | ----------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **SHINC**    | Sundays and Holidays **Included**                     | Laytime counts on Sundays and holidays                                                  |
| **SHEX**     | Sundays and Holidays **Excluded**                     | Laytime does **not** count on Sundays and holidays                                      |
| **FHEX**     | Fridays and Holidays Excluded                         | Variant for Muslim-country ports                                                        |
| **WWD**      | Weather Working Days                                  | Only counts time when weather permits work; bad weather stops the clock                  |
| **WWDSHINC** | Weather Working Days, Sundays and Holidays Included   | Common composite                                                                        |
| **WWDSHEX**  | Weather Working Days, Sundays and Holidays Excluded   | Common composite                                                                        |
| **WPD**      | Weather Permitting Days                               | Similar to WWD but with slight contractual differences                                  |
| **WIBON**    | Whether In Berth Or Not                               | NOR can be tendered even if vessel cannot berth (e.g., congestion). Critical clause.    |
| **WIPON**    | Whether In Port Or Not                                | Even broader — NOR can be tendered before entering port. Rare.                          |
| **WIFPON**   | Whether In Free Pratique Or Not                       | Free pratique not required for valid NOR                                                |
| **WICCON**   | Whether In Customs Clearance Or Not                   | Customs not required for valid NOR                                                      |

## 4. Foundational rules to bake into the calculator

### Once on demurrage, always on demurrage
Once laytime expires and the vessel goes on demurrage, exception clauses generally stop applying. Bad weather doesn't pause the demurrage clock unless the CP says so. This is a critical rule — surfacing it correctly is a tell that we know what we are doing.

### Reversible vs non-reversible laytime
"Reversible" means load and discharge laytime allowances can be combined. "Non-reversible" means they are separate buckets. Default depends on the CP form.

### Laycan window
"Laydays / Cancelling" — the contractual window during which the vessel must arrive and tender NOR. If the vessel arrives before laydays, the charterer is not obliged to accept NOR. If after the cancelling date, the charterer can cancel the fixture.

### Time bar
**This is the most important commercial fact in the entire industry.** Charter parties typically require the demurrage claim to be submitted within a strict window from completion of discharge — commonly 90 days for tanker trades — with all original supporting documents. Miss the time bar by even one day and the entire claim is forfeit, regardless of merit.

Portside must surface the time bar clock the moment the voyage is loaded. **This is the single biggest avoidable loss in the industry and is the most important UX moment in our product.**

### Free pratique
Clearance by port health authorities. Many CPs treat free pratique as a prerequisite for valid NOR (unless WIFPON applies).

### Shifting time
Time spent shifting between anchorage and berth, or between berths. Whether it counts as laytime depends on the CP and on the reason for shifting.

## 5. Common dispute patterns (the contests our agent must handle)

These are the five archetypes our Dispute Analyst should know cold:

1. **NOR validity dispute.** Was the NOR tendered when the vessel was actually ready? Was free pratique granted? Was it tendered during permitted hours? Was the vessel at the correct location?

2. **Weather exception dispute.** Did the weather actually stop work? Charterer claims rain stopped cargo ops for 11 hours; port authority's weather record shows precipitation was below the threshold defined in the CP. **This is our demo dispute.**

3. **SHINC vs SHEX interpretation.** What counts as a "holiday" in the port jurisdiction? Local religious holidays? Bank holidays? Strikes?

4. **Waiting for berth (WIBON / port congestion).** Vessel arrives, can't berth because of congestion. Under WIBON, NOR is valid and the time counts. Without WIBON, owner may eat the waiting time.

5. **Once on demurrage, always on demurrage.** Charterer tries to claim a weather exception while vessel is already on demurrage. Owner disputes — exceptions don't apply post-demurrage unless explicit in CP.

## 6. Numbers, units, and conventions to get right

- **Demurrage rates** are quoted in USD per day or per day pro rata (PDPR — partial days charged proportionally).
- **Laytime** is quoted in hours or days. "72 running hours" means 72 consecutive clock hours including weekends. "3 weather working days" means 3 days that count as weather working.
- **Time precision** — to the minute, not the hour. SoFs record "1437 LT" (local time) routinely. Round only at final output.
- **Time zone** — SoFs use port local time. CP rates are in USD. The claim letter uses port local time + UTC offset.
- **Currency** — almost always USD in international tanker trades.
- **Day of week** — the calculator needs the day-of-week of every event because of SHEX. We will use the port's local timezone.

## 7. Anatomy of a claim letter (what Agent 4 must produce)

A BIMCO-style demurrage claim letter has these sections, in this order:

1. **Header** — owner's company, charterer's company, voyage reference, vessel name, CP date, claim date.
2. **Subject line** — e.g., "Demurrage Claim — MV [VESSEL] — [LOAD PORT] / [DISCHARGE PORT] — CP dated [DATE]".
3. **Opening** — formal salutation, identification of the voyage and CP.
4. **Laytime summary** — laytime allowed, laytime used, time on demurrage, demurrage rate, total claim.
5. **Calculation table** — per-event time accounting (we will include this as an annexure reference).
6. **Time bar statement** — explicit statement that the claim is submitted within the contractual time bar, with the time bar date noted.
7. **Supporting documents list** — Charter Party, Notice of Readiness, Statement of Facts, port log extract, weather records (where relevant).
8. **Demand for payment** — the dollar amount, the bank details (placeholder), the payment deadline.
9. **Reservation of rights** — standard boilerplate.
10. **Signature block** — claims executive name, company, date.

The judge will read the letter. It must look like it came from a real claims department.

## 8. Glossary of acronyms you will see

- **CP** — Charter Party
- **NOR** — Notice of Readiness
- **SoF** — Statement of Facts
- **VLCC** — Very Large Crude Carrier (200k–320k DWT tanker)
- **DWT** — Deadweight tonnage (the cargo + bunkers + stores capacity of a vessel)
- **LT** — Local Time (on SoF timestamps)
- **PDPR** — Per Day Pro Rata
- **P&I** — Protection & Indemnity (the clubs that handle owner liability)
- **BIMCO** — Baltic and International Maritime Council (publishes standard forms)
- **LMAA** — London Maritime Arbitrators Association (handles many disputes)
- **All fast** — vessel fully moored at berth
- **Tender** — to formally hand over the NOR (verb)

## 9. Sources we are using

- **BIMCO** publishes standard forms publicly (ASBATANKVOY, NYPE 93, GENCON, Shellvoy). Pull clause language from these.
- **International Group of P&I Clubs** publishes educational material on laytime and demurrage.
- **TotalEnergies, Shell, BP** publish voyage charter guidance documents with worked SoF examples.

We do not need a single real customer dataset for the demo.
