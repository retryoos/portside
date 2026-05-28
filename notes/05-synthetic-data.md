# Synthetic Data — the demo voyages

> One hour of work in the morning. Five scenarios. The first one (Rotterdam weather dispute) is what we demo. The other four are backup.

We are not faking. The synthetic documents must look real to a maritime professional skimming them for 10 seconds. That means correct vocabulary, BIMCO-style layout, plausible vessel and port names, and timestamps that actually line up across the three documents.

---

## 1. The primary demo scenario — `rotterdam-weather-dispute`

### Why this one
- Lands in Europe at Rotterdam — the biggest tonnage port on the continent and a name every judge will recognise.
- The dispute is the most visually compelling: a contested 4-hour weather stoppage on 17 May worth EUR 7,500. That contested row is the "aha moment" — the agent flags it, cites CP clause 14, and shows why the charterer's exception fails.
- Doesn't require any exotic clauses. ASBATANKVOY-style language is sufficient.

### Voyage details

| Field                   | Value                                            |
| ----------------------- | ------------------------------------------------ |
| Vessel                  | MT Aegean Pioneer (fictional VLCC)               |
| Owner                   | Aegean Tankers S.A.                              |
| Charterer               | North Sea Crude Trading B.V.                     |
| CP form                 | ASBATANKVOY                                      |
| CP date                 | 12 February 2026                                 |
| Load port               | Ras Tanura, Saudi Arabia                         |
| Discharge port          | Rotterdam, Netherlands                           |
| Laytime allowed         | 72 hours SHINC (discharge)                       |
| Demurrage rate          | EUR 45,000 per day pro rata (= EUR 1,875/hr)     |
| Despatch rate           | EUR 22,500 per day pro rata                      |
| Exception clauses       | WIBON, WIFPON, SHINC                             |
| Special weather clause  | **Clause 14** — weather stoppages count only where precipitation > 0.5 mm/hr |
| Time bar                | 90 days from completion of discharge             |

### Discharge timeline at Rotterdam

| Event ID | Local time             | Description                                         |
| -------- | ---------------------- | --------------------------------------------------- |
| e1       | 2026-05-14 05:00       | Arrived at Maasvlakte anchorage                     |
| e2       | 2026-05-14 06:00       | NOR tendered                                        |
| e3       | 2026-05-14 12:00       | Laytime commenced                                   |
| e4       | 2026-05-14 20:00       | All fast at berth                                   |
| e5       | 2026-05-14 22:00       | Commenced discharge                                 |
| e6       | 2026-05-17 12:00       | Stoppage — rain claimed by charterer                |
| e7       | 2026-05-17 16:00       | Resumed discharge                                   |
| e8       | 2026-05-19 09:00       | Completed discharge                                 |

Charterer claims event e6 → e7 (4 hours) is excepted weather time. Owner disputes because the Rotterdam Port Authority precipitation record shows a maximum of 0.2 mm/hr at the relevant times — below the 0.5 mm/hr threshold in CP clause 14. The position is backed by *The Mexico 1* [1990] 1 Lloyd's Rep 507.

Numbers:
- Laytime allowed: 72 hours
- Laytime used (owner's view, 4h disputed counts): 117 hours → 45 hours on demurrage = EUR 84,375.00
- Laytime used (charterer's view, 4h excepted): 113 hours → 41 hours on demurrage = EUR 76,875.00
- Delta: EUR 7,500 — incremental recoverable on the contested 4-hour window
- Final claim (owner): **EUR 84,375.00**

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

> Implementation note (May 28): the primary scenario's generator landed in `synthetic-data/generate.py` using `fpdf2` instead of `weasyprint` — pure Python, no native deps. Either approach satisfies the "looks like a contract / SoF / NOR" bar.

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
- [ ] The Agent 3 flagged-events output mentions clause 14 by name and the 0.5 mm/hr precipitation threshold
- [ ] The Agent 4 letter cites the time bar date (17 August 2026 — 90 days from completion of discharge), the supporting documents list, and the BIMCO-style demand
- [ ] End-to-end runtime is under 60 seconds on the demo laptop's network

If any of these fail, fix them before doing anything else.
