"""Local PDF text extraction (upstream of Agent 1).

Each uploaded PDF is turned into clean text with pdfplumber BEFORE any LLM call,
so Claude never pays the vision-token surcharge and Agent 1 runs on text. Tables
(the SoF event grid) are flattened to pipe-delimited rows. See
notes/03-agents.md "PDF text extraction".

If pdfplumber returns nothing (scanned/undecodable PDF), `extract_pdf_text`
returns "" and the caller falls back to attaching the raw PDF as a Claude
`document` content block.
"""

from __future__ import annotations

import io

import pdfplumber


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Return the text + flattened tables of a PDF, or "" if nothing extractable."""
    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
            for table in page.extract_tables():
                parts.append(
                    "\n".join(
                        " | ".join((cell or "") for cell in row) for row in table
                    )
                )
    return "\n\n".join(p for p in parts if p).strip()


def extract_all(documents: dict[str, bytes]) -> dict[str, str]:
    """Extract text for each uploaded document, keyed by role ('cp'/'nor'/'sof')."""
    return {role: extract_pdf_text(blob) for role, blob in documents.items()}
