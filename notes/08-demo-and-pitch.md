# Demo Script and Finalists Pitch

> The only two things that matter at 19:00 and 20:30. Both are short. Both must be rehearsed at least twice.

---

## Part 1 — The 5-minute demo (19:00)

### Setup before walking on
- Demo laptop on, browser fullscreen at `http://localhost:3000`, blank state.
- The three demo PDFs are on the desktop in a folder labeled clearly.
- Backend running on `http://localhost:8000`, terminal closed, only the browser visible.
- Backup video queued in another browser tab in case the live run dies.

### Beat 1 — Frame the problem (45s)

> "Every time a vessel finishes a port call and the laytime is disputed, somebody on the operator's team spends two to four days assembling the Charter Party, the Statement of Facts, and the Notice of Readiness, calculating which hours count against laytime and which don't, then writing a claim letter that may or may not survive the counterparty's pushback. A single VLCC sitting idle is thirty to eighty thousand dollars per day. The industry's annual demurrage exposure is in the billions."
>
> "Excel and specialist P&I advisors are the state of the art. Neither is a product."
>
> "Portside is the product."

### Beat 2 — Show the upload (30s)

> "Owner's team gets the voyage docs from the port agent and the master. They drop them on Portside."

Drag the three PDFs onto the dropzone. Documents appear in the left panel. Vessel name and voyage ID appear in the top bar. Time-bar badge appears: **88 days remaining**.

> "Right away you see the time-bar countdown. Demurrage claims have a strict contractual deadline — usually 90 days from completion of discharge with all original documents. Miss it by one day, the entire claim is forfeit, regardless of merit. That is the single biggest avoidable loss in this industry. We surface it the moment the voyage is loaded."

### Beat 3 — The agent run (45s)

The center panel shows the four-step agent indicator running:

```
[✓ Extract docs]  [✓ Calculate laytime]  [● Analyze disputes]  [○ Draft claim]
```

> "Four agents. The first extracts the structured fields from each document. The second classifies each Statement of Facts event against the charter party's exception clauses — SHINC, SHEX, WIBON, weather. The third identifies the contestable time windows and writes the legal argument. The fourth drafts the formal claim letter."
>
> "One detail that matters: the arithmetic is done in deterministic Python, not by the LLM. The model classifies. Python sums. A claims executive would not trust an LLM to add up hours. They will trust this."

Center panel fills with the laytime table. Bottom shows:

```
DEMURRAGE DUE TO OWNERS
USD 38,400.00
Laytime allowed 72h · Used 89.5h · On demurrage 17.5h
```

### Beat 4 — The winning moment (60s)

Click the amber-flagged row in the laytime table — the 11-hour weather stoppage on 10 May.

> "Here is the contested time. The charterer claimed an eleven-hour weather stoppage. Charter party clause 17 admits weather exceptions only when sustained wind speeds exceed twenty-five knots. The Piraeus port authority's weather record for that day shows peak gusts of eighteen knots and no rain at the relevant times."

The inline expansion shows:

```
⚑  Weather exception not supported by CP clause threshold
   Owner's position: 88% confidence
   Incremental recoverable demurrage: USD 22,000
   Citations: CP clause 17; SoF event e6
```

> "Eighty-eight percent confidence on the owner's position. Twenty-two thousand dollars of incremental recoverable demurrage in this one disputed window. The agent cites the specific clause and the specific event. A real claims associate could take this argument straight to the counterparty."

### Beat 5 — The claim letter (45s)

Click **Generate Claim Letter** in the right panel. The BIMCO-style letter streams in.

> "And this is the output. A formal demurrage claim letter, BIMCO-style language, time-bar statement, supporting documents list, demand for payment, reservation of rights. Exportable as PDF or Word."

### Beat 5.5 — The professional in the loop (60s, **stretch — only if landed**)

> *(Land this beat only if [13-inline-revision.md](13-inline-revision.md) shipped. Otherwise skip to Beat 6 and hand the printed letter to the nearest judge.)*

Highlight the second paragraph of the letter — the one describing the weather dispute. The **Refine** toolbar appears anchored to the selection.

> "Portside drafts the letter. The claims executive owns it. Suppose they want the clause citation up front, not buried."

Click **Refine**. The inline panel opens. Type into the textarea: *"Lead with the citation to CP clause 17 and mention the 25-knot threshold explicitly."* Click **Refine with AI**. A loading pulse runs for ~1.5 seconds.

> "The agent rewrites only this paragraph. The dollar amount is locked — it cannot be changed by a re-prompt. The clause citations are preserved. The time-bar statement is locked. Everything else is editable in place, by AI or by hand. Every revision is logged. Every export carries the audit trail."

Paragraph replaces with the revised version. An `✎ edited` mark appears in the margin.

> "The claims executive isn't replaced. They are multiplied."

Hand the printed PDF to the nearest judge.

### Beat 6 — Close (35s)

> "Two days of work compressed into one minute. Two thousand dollars per hour of incremental recoverable demurrage that today either gets left on the table because the claim is too slow, or gets settled at half its real value because the legal argument was thin."
>
> "Greece controls twenty percent of global merchant fleet tonnage. Piraeus is the largest port in the Mediterranean. The dollar volume on the table is in the billions every year. Portside is the first product built for this workflow."
>
> "Thank you."

---

## Part 2 — Anticipated judge questions

The judge that "handles these things for all companies" will dig. Be ready.

**Q: How do you know your laytime calculation is correct?**
A: The arithmetic is deterministic Python — not the LLM. The LLM classifies each event against the charter party's exception clauses and a deterministic walker accumulates time. We unit-test the walker against worked examples from BIMCO and P&I club guidance.

**Q: What stops the model from hallucinating a clause that doesn't exist?**
A: The dispute analyst cites clauses by number. Each citation is checked back to the actual extracted clause text from Agent 1. If the clause number is not in the extraction, the citation fails validation and we re-prompt.

**Q: What about charter parties that use custom or non-BIMCO language?**
A: For the MVP we target ASBATANKVOY, GENCON, NYPE 93, and Shellvoy — the four standard forms that cover most tanker and dry voyages. Non-standard CPs are a roadmap item. We can ingest non-standard CPs at lower confidence and surface the confidence to the user.

**Q: How does it handle "once on demurrage, always on demurrage"?**
A: It's encoded in the calculator. Once the running laytime total crosses the allowance, exception clauses stop applying unless the CP explicitly provides otherwise. We flag any exception claimed during demurrage as contestable with high owner-position strength.

**Q: What is your moat? An LLM company could build this.**
A: Three layers. First, the synthesis of charter party clause language, port-jurisdiction holiday calendars, BIMCO conventions, and historical dispute patterns — encoded in our prompts and rule library. Second, the fleet-specific company brain — every voyage processed teaches us your preferred clause language, your typical dispute outcomes, and your counterparty patterns. Third, the AI-native service motion — we can run the claim end-to-end on a success fee basis, capturing economic value that pure software cannot.

**Q: Who is the buyer? Operators? Charterers? Lawyers?**
A: Day one, ship operators and charterers in Greece — there are hundreds of ship management companies in Athens alone, and our buyer is a head of operations or head of claims. Year two, maritime law firms and P&I clubs. The same engine powers all three.

**Q: How accurate does it have to be to be useful?**
A: It does not have to be perfect — a claims executive will review every output before sending. It has to be **defensible**. Every figure traceable to a source event. Every argument citing a specific clause. A demurrage claim that the counterparty cannot reflexively reject is worth its weight even if the executive edits 10% of it.

**Q: What if the counterparty has Portside too?**
A: Excellent — that is the second motion. We sell to both sides. The output of both sides feeds into a shared arbitration record. Today these disputes go to LMAA arbitration with paper folders and human advocates. We compress that loop too.

**Q: How long until you have a paying customer?**
A: We have validation from a Greek shipping executive who saw a build of the agent. The path from here is a paid pilot with one Greek operator at thirty days, three at ninety, ten by end of year. Greek shipping is a tight community — one happy operator is the difference between a cold-call business and a referral business.

**Q: What is the technical risk?**
A: The hardest technical surface is the prompt engineering for the dispute analyst — getting an LLM to write like a maritime lawyer, citing clauses correctly, in a style that survives counterparty scrutiny. We have de-risked this by separating concerns: the LLM does extraction and classification and drafting; the arithmetic and citation validation are deterministic.

---

## Part 3 — The finalists pitch (20:30, ~3 minutes)

Different from the demo. No screen. Just the team standing up and talking.

### Beat 1 — The hook (20s)
> "There is one Greek industry where a single mistake costs eighty thousand dollars a day. It is not shipping. It is paperwork about shipping. Every contested demurrage claim is a paper fight that takes days, and Greek shipowners — who control a fifth of the world's tonnage — are losing billions of dollars a year because the paper fight is slower than the claim deserves to be."

### Beat 2 — The product (40s)
> "Portside turns that paper fight into a one-minute workflow. Three voyage documents in. A defensible, BIMCO-style claim packet out. Per-event laytime calculation with deterministic arithmetic. Legal arguments for each contested time window with charter party clause citations. A formal claim letter ready to send. Today this takes two to four days of specialist time. Portside does it in under sixty seconds."

### Beat 3 — Why now, why us (40s)
> "Two things changed. One, frontier models can now reason about contractual language and event timelines well enough that the synthesis is finally tractable. Two, the maritime industry's center of gravity for these disputes is in this room. Athens controls twenty percent of global tonnage. We showed an early build to a senior executive at a major Greek shipping company and to a shipping-industry adjudicator. Both said the same thing: this is the missing tool."

### Beat 4 — The business (40s)
> "Two motions, both already proven in other domains. SaaS at five hundred to two thousand dollars per seat per month, sold to operators, charterers, and maritime lawyers. And the AI-native service motion — we run the claim end-to-end on a success fee. Hundreds of ship management companies in Greece alone. Every voyage processed grows a proprietary dataset on clause language, dispute outcomes, and counterparty patterns. The deeper this engine runs, the harder it gets to replicate."

### Beat 5 — The ask (20s)
> "We built this in twelve hours. The next twelve days are about turning it from a clean demo into a paid pilot with a Greek operator. The twelve months after that are about being the company that the maritime industry trusts with its contested time. Thank you."

---

## Logistics for both presentations

- **One person presents.** The other two stand behind. No rotation.
- **Demo run only on the demo laptop.** Tested twice in the same room before going on stage.
- **Have the backup video ready.** Pre-launched, paused on frame 0.
- **The printed claim letter.** If the venue allows, bring one printed copy of the BIMCO letter to hand to a judge. The tactile evidence is disproportionately persuasive.
- **No emojis on screen. No memes. No GIFs.** This is a maritime industry audience.
- **Spell out dollar amounts.** "USD 22,000" or "twenty-two thousand dollars" — not "$22k."
- **Use port local time on timestamps.** "08 May 13:00 LT" — that's how the industry writes it.
