# Synthetic Data — the demo voyages

> One hour of work in the morning. Five scenarios. The first one (Piraeus weather dispute) is what we demo. The other four are backup.

We are not faking. The synthetic documents must look real to a maritime professional skimming them for 10 seconds. That means correct vocabulary, BIMCO-style layout, plausible vessel and port names, and timestamps that actually line up across the three documents.

---

## 1. The primary demo scenario — `athens-weather-dispute`

### Why this one
- Lands in Athens. The judges will know Piraeus.
- The dispute is the most visually compelling: an 11-hour weather stoppage the charterer claimed but the port weather record contradicts. The agent's flag and the dollar increment ($2,200 of incremental demurrage on top of $33k base = $35,200 total claim — final demo total of `USD 35,000` or `USD 38,400`) is a clean "aha moment."
- Doesn't require any exotic clauses. ASBATANKVOY-style language is sufficient.

### Voyage details

| Field                   | Value                                            |
| ----------------------- | ------------------------------------------------ |
| Vessel                  | MV Anthem of Piraeus (fictional VLCC, 320k DWT)  |
| Owner                   | Hellas Shipping Co.                              |
| Charterer               | Mediterranean Crude Trading                      |
| CP form                 | ASBATANKVOY 1977 (amended)                       |
| CP date                 | 12 April 2026                                    |
| Load port               | Ras Tanura, Saudi Arabia                         |
| Discharge port          | Piraeus, Greece                                  |
| Laytime allowed         | 72 hours SHINC (discharge)                       |
| Demurrage rate          | USD 48,000 per day pro rata                      |
| Despatch rate           | USD 24,000 per day pro rata                      |
| Exception clauses       | WIBON, WIFPON                                    |
| Special weather clause  | Clause 17 — weather stoppages count only when sustained wind > 25 knots |
| Time bar                | 90 days from completion of discharge             |

### Discharge timeline at Piraeus

| Event ID | Local time             | Description                                         |
| -------- | ---------------------- | --------------------------------------------------- |
| e1       | 2026-05-08 06:30       | Arrived at customary anchorage                      |
| e2       | 2026-05-08 07:00       | NOR tendered                                        |
| e3       | 2026-05-08 13:00       | Laytime commenced (6 hours after NOR)               |
| e4       | 2026-05-09 02:00       | All fast at berth                                   |
| e5       | 2026-05-09 04:00       | Commenced discharge                                 |
| e6       | 2026-05-10 11:00       | Charterer-claimed weather stoppage begins (rain)    |
| e7       | 2026-05-10 22:00       | Resumed discharge                                   |
| e8       | 2026-05-11 18:30       | Laytime expires (72 hours from e3)                  |
| e9       | 2026-05-12 12:00       | Completed discharge                                 |

Charterer claims event e6 → e7 (11 hours) is excepted weather time. Owner disputes because port authority record shows peak gust of 18 knots — below the 25-knot threshold in clause 17.

Numbers:
- Laytime allowed: 72 hours
- Time excepted (charterer's view): 11 hours from e6→e7
- Time used (charterer's view): ~95 - 11 = 84 hours → 12 hours of demurrage = USD 24,000
- Time used (owner's view, with e6→e7 disallowed): 95 hours → 23 hours of demurrage = USD 46,000
- Delta: USD 22,000 — **this is the dollar figure we put on screen as "incremental recoverable"**
- Final claim (owner): **USD 46,000** (or rounded to 38,400 / 35,000 for narrative simplicity — pick one and stay consistent across docs)

> **Decision to make on the morning:** lock the exact dollar figures in `apps/api/portside_api/fixtures/athens_weather/` and make sure the synthetic CP, SoF, and weather record all reconcile to them.

---

## 2. Backup scenarios (in case the primary breaks during the demo)

### `nor-tender-dispute`
- NOR tendered at 0530 LT but CP says NOR must be tendered between 0600–1800 LT.
- Owner re-tenders at 0600.
- Dispute: does laytime run from the invalid 0530 tender, the valid 0600 re-tender, or from commencement of cargo ops?
- Agent surfaces: "NOR at 0530 invalid per CP clause 6; laytime commences from 0600 re-tender + 6 hours."

### `shinc-shex-dispute`
- CP is ambiguous on whether the local Orthodox holiday on the discharge date counts as a "holiday."
- Dispute: charterer claims 24 hours of SHEX exception for the holiday; owner argues the day was a normal working day at the port.
- Agent surfaces: clause language + port-jurisdiction guidance.

### `congestion-wibon-dispute`
- Vessel arrives, berth occupied, waits 36 hours at anchorage.
- CP has WIBON but charterer claims NOR cannot be valid because vessel was not at berth and free pratique was delayed.
- Dispute: does WIBON + WIFPON cover the waiting time?
- Agent surfaces: WIBON clause carries the waiting time, WIFPON disposes of the free-pratique argument.

### `on-demurrage-exception`
- Vessel goes on demurrage at hour 72.
- At hour 78, a rain stoppage occurs.
- Charterer claims 4 hours of weather exception during demurrage.
- Owner argues: once on demurrage, always on demurrage — exception does not apply.
- Agent surfaces: the foundational rule with citation.

---

## 3. How to generate the PDFs

One Python script: `synthetic-data/generate.py`. For each scenario:

1. Render a Charter Party excerpt as a 2-page PDF — recitals, the laytime/demurrage clauses, and a couple of the relevant exception clauses (especially clause 17 for the weather case). Use a serif font (e.g., Crimson Text) and number the paragraphs. Look like a contract.
2. Render a Statement of Facts as a 4-page PDF — port name, vessel name, voyage number at the top; a table of events with timestamps in `HH:MM LT` format and a description column; signature blocks at the end. Look like a port agent's signed log.
3. Render a Notice of Readiness as a 1-page PDF — letterhead-style header, the formal text ("Please take this as Notice that the captioned vessel arrived..."), tendered/accepted times, signature block.

Generation approach options, in order of preference:
- **(Preferred) HTML + weasyprint.** `weasyprint` is used here as a **dev-time tool only** — to generate the synthetic input PDFs once. It runs on a Mac or under WSL on the Windows box (where its cairo/pango deps install cleanly via `brew`/`apt`). It is **not** part of the product runtime — the output claim letter is exported client-side in the browser, so `weasyprint` never ships to App Runner and never needs to run on native Windows. Templates live alongside the scenario JSON.
- **(Backup) Word docs by hand.** Write three docs in Word, export to PDF, swap in the values per scenario. Faster if `weasyprint` HTML styling eats too much time, and avoids the dependency entirely.
- **(Also fine) Browser print.** Open the HTML scenario template in a browser and print-to-PDF. Zero dependencies; works on any machine.

The point is not perfection. The point is: a maritime person skimming for 5 seconds reads "yeah, that's a SoF."

---

## 4. Pre-flight checks for the demo scenario

By 17:00 on May 28th, verify on the primary scenario:

- [ ] All three PDFs open and render readably
- [ ] All cross-references reconcile (vessel name, owner, charterer, dates, ports)
- [ ] The Agent 1 extraction round-trips: every field in the schema gets populated
- [ ] The Agent 2 arithmetic produces exactly the planned dollar figure
- [ ] The Agent 3 flagged-events output mentions clause 17 by name and the 25-knot threshold
- [ ] The Agent 4 letter cites the time bar date, the supporting documents list, and the BIMCO-style demand
- [ ] End-to-end runtime is under 60 seconds on the demo laptop's network

If any of these fail, fix them before doing anything else.
