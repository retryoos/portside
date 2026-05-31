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

import time
from collections import deque

from fastapi import HTTPException, Request, UploadFile

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


def client_key(request: Request) -> str:
    """Best-effort caller identity for rate limiting.

    Behind App Runner / a load balancer the real client sits in the first hop
    of ``X-Forwarded-For``; fall back to the socket peer otherwise. This is a
    coarse key (a NAT'd office shares one), which is the right tradeoff for an
    abuse/cost guard — it is not an auth boundary.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


class SlidingWindowRateLimiter:
    """In-process sliding-window rate limiter (one event loop, single instance).

    Tracks request timestamps per key in a deque and rejects once the count
    within ``window_seconds`` reaches ``max_requests``. State is process-local,
    which matches the single App Runner instance; a multi-instance deploy would
    move this to a shared store (Redis). Set ``max_requests <= 0`` to disable.

    ``allow`` runs entirely synchronously (no awaits between read and write), so
    it is safe under the asyncio event loop without a lock.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}

    @property
    def enabled(self) -> bool:
        return self.max_requests > 0

    def allow(self, key: str, *, now: float | None = None) -> bool:
        if not self.enabled:
            return True
        now = time.monotonic() if now is None else now
        window_start = now - self.window_seconds
        hits = self._hits.get(key)
        if hits is None:
            hits = deque()
            self._hits[key] = hits
        while hits and hits[0] <= window_start:
            hits.popleft()
        if len(hits) >= self.max_requests:
            if not hits:
                # Defensive: max_requests<=0 is handled above, so an empty
                # deque can't trip this; keep the map from growing unbounded.
                self._hits.pop(key, None)
            return False
        hits.append(now)
        return True
