"""Generate the demo voyage PDFs (Rotterdam scenario) + expected.json.

Dev-time only. Produces text-native PDFs (fpdf2 — no native deps) that, when run
through pdfplumber + the agent pipeline, reconcile to the single source of truth:
MT Aegean Pioneer, Ras Tanura -> Rotterdam, EUR 84,375.00.

Usage:
    pip install -r synthetic-data/requirements.txt
    python synthetic-data/generate.py

Writes to synthetic-data/scenarios/rotterdam-weather-dispute/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

_ROOT = Path(__file__).resolve().parent
_OUT = _ROOT / "scenarios" / "rotterdam-weather-dispute"

CHARTER_PARTY = """CHARTER PARTY (ASBATANKVOY) — EXCERPT

Dated: 12 February 2026
Vessel: MT Aegean Pioneer
Owner: Aegean Tankers S.A.
Charterer: North Sea Crude Trading B.V.
Load port: Ras Tanura
Discharge port: Rotterdam

Laytime allowed: 72 running hours, SHINC.
Demurrage rate: EUR 45,000.00 per day, pro rata.
Despatch rate: EUR 22,500.00 per day.
Exception clauses in force: WIBON, WIFPON, SHINC.
NOR may be tendered any time, day or night, SHINC.
Time bar: 90 days from completion of discharge.

Clause 6 — Commencement of laytime.
Laytime shall commence 6 hours after tender of Notice of Readiness, berth or no
berth, or upon commencement of cargo operations, whichever first occurs.

Clause 14 — Weather.
Time lost due to rain or other weather conditions shall not count as laytime only
where precipitation at the place of discharge exceeds 0.5 mm per hour for the
period claimed. The burden of demonstrating such conditions rests with the
charterer.
"""

NOTICE_OF_READINESS = """NOTICE OF READINESS

Vessel: MT Aegean Pioneer
Port: Rotterdam (Maasvlakte customary anchorage)
Tendered to: North Sea Crude Trading B.V.
Tendered by: Master, MT Aegean Pioneer

Tendered at: 14 May 2026, 06:00 hours (+02:00)
Accepted at: 14 May 2026, 06:00 hours (+02:00)
Free pratique granted: 14 May 2026, 07:30 hours (+02:00)
Berth status at tender: berth occupied
"""

STATEMENT_OF_FACTS = """STATEMENT OF FACTS

Vessel: MT Aegean Pioneer
Port: Rotterdam
Timezone: Europe/Amsterdam

TIMESTAMP            | DESCRIPTION                              | CATEGORY
2026-05-14 05:00 +02 | Arrived at Maasvlakte anchorage          | arrival
2026-05-14 06:00 +02 | NOR tendered                             | nor
2026-05-14 12:00 +02 | Laytime commenced                        | laytime start
2026-05-14 20:00 +02 | All fast at berth                        | berthing
2026-05-14 22:00 +02 | Commenced discharge                      | ops start
2026-05-17 12:00 +02 | Stoppage - rain claimed by charterer     | weather stoppage
2026-05-17 16:00 +02 | Resumed discharge                        | ops resume
2026-05-19 09:00 +02 | Completed discharge                      | ops end
"""


# fpdf2's built-in Helvetica is latin-1 only; map common Unicode punctuation to
# ASCII so the text-native PDFs render (and pdfplumber reads them) cleanly.
_ASCII_MAP = {
    ord("—"): "-", ord("–"): "-", ord("’"): "'", ord("‘"): "'",
    ord("“"): '"', ord("”"): '"', ord("§"): "Sec ", ord("·"): "-",
    ord("…"): "...",
}


def _ascii(s: str) -> str:
    return s.translate(_ASCII_MAP).encode("latin-1", "replace").decode("latin-1")


def _write_pdf(text: str, path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in text.splitlines():
        pdf.multi_cell(0, 5, _ascii(line) if line else " ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(path))


def _write_expected_json(path: Path) -> None:
    # Import the canonical fixture (single source of truth) and dump it.
    sys.path.insert(0, str(_ROOT.parent / "apps" / "api"))
    from portside_api.fixtures import demo_voyage_fixture  # noqa: E402

    state = demo_voyage_fixture()
    path.write_text(state.model_dump_json(by_alias=True, indent=2))


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    _write_pdf(CHARTER_PARTY, _OUT / "Charter Party.pdf")
    _write_pdf(NOTICE_OF_READINESS, _OUT / "Notice of Readiness.pdf")
    _write_pdf(STATEMENT_OF_FACTS, _OUT / "Statement of Facts.pdf")
    _write_expected_json(_OUT / "expected.json")
    print(
        "Wrote 'Charter Party.pdf', 'Notice of Readiness.pdf', "
        f"'Statement of Facts.pdf', expected.json to {_OUT}"
    )


if __name__ == "__main__":
    main()
