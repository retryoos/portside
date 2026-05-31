"""Outbound email for claim packets (notes/architecture_weeks_5_to_8.md §1.3).

Single integration today: AWS SES via boto3. The send path is wrapped so the
route layer never imports boto3 directly and tests never touch the network.

Public surface
--------------

- ``send_claim_letter(state, request) -> SesSendResult``: async wrapper that
  off-threads the boto3 call. Returns the SES message id on success; on
  failure raises ``EmailSendError`` with an actionable error code.
- ``EmailSendError``: error code enum maps to the HTTP status the route
  surfaces (sandbox = 422, throttling = 429, transport = 502).
- ``LetterEmailRequest``: request shape consumed by ``POST
  /voyages/{id}/letter/email``.

Wired off by default
--------------------

When ``settings.email_send_live`` is False, ``send_claim_letter`` records the
attempt and returns a synthetic result with ``ses_message_id="sandbox"``. This
lets the route be exercised end-to-end in dev without an SES identity, and
lets tests assert the surface without mocking boto3 client internals.
"""

from .models import (
    EmailErrorCode,
    EmailSendError,
    LetterEmailRequest,
    SesSendResult,
)
from .ses import build_mime, send_claim_letter

__all__ = [
    "EmailErrorCode",
    "EmailSendError",
    "LetterEmailRequest",
    "SesSendResult",
    "build_mime",
    "send_claim_letter",
]
