"""Upload size and content-type limits for POST /voyages (P9 minimum slice).

Enforces a per-file size cap and a content-type allowlist before the request
ever reaches the pipeline. The full P9 hardening (rate limits, pipeline
timeout audit, error taxonomy, DB backup policy) is Tier 2 work; this module
is the smallest viable guard against an investor-facing accidental DoS or a
non-PDF upload that would crash the extractor.

Contract:
    POST /voyages rejects with 415 if any file's content-type is not
    application/pdf, and rejects with 413 if any file exceeds the size cap.
    Neither path ever reaches object storage or the pipeline.

Constants stay tiny and explicit so a future Tier 2 PR can subclass or
replace this module without touching call sites.
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
"""Per-file upload cap on POST /voyages. 25 MiB. Real voyage PDFs are well
under this; an investor demo doesn't need bigger and a 100 MB upload from a
mis-clicked drag-and-drop should not tie up the box."""

ALLOWED_CONTENT_TYPES = frozenset({"application/pdf"})
"""Allowlisted content-types. The pipeline's pdfplumber stage assumes PDF,
so anything else is rejected early to keep error messages crisp."""


async def validate_and_read(upload: UploadFile, *, role: str) -> bytes:
    """Validate the content-type and size, then return the bytes.

    Reads up to ``MAX_UPLOAD_BYTES + 1`` bytes so we can distinguish
    at-the-limit from over-the-limit without ever holding more than one
    extra byte in memory. ``role`` (one of "cp", "nor", "sof") is folded
    into the error detail so a frontend can point at the right slot.

    Raises:
        HTTPException 415 if ``upload.content_type`` is missing or not in
            ``ALLOWED_CONTENT_TYPES`` (a .docx is rejected here, never
            reaching disk).
        HTTPException 413 if the body exceeds ``MAX_UPLOAD_BYTES``.
    """
    ctype = upload.content_type or ""
    if ctype not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"unsupported content-type for {role}: "
                f"{ctype or '(missing)'}; expected application/pdf"
            ),
        )
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"{role} exceeds the "
                f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MiB upload cap"
            ),
        )
    return data
