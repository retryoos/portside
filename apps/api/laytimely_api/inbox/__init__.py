"""Email-in ingestion (notes/architecture_weeks_5_to_8.md §2.3).

The route accepts a forwarded RFC 822 message (from AWS SES → S3 → Lambda in
production; from a local dev SMTP harness on a laptop) and creates or matches
a voyage from its PDF attachments. The boundary is one HMAC-signed header so
the route can sit behind no other auth: SES does not authenticate the way
Cognito does, so we replace that with a shared secret the Lambda holds and
the route verifies in constant time.

Public surface
--------------

- ``InboundMessage``: parsed view of one forwarded email.
- ``parse_message(raw_bytes)``: pure parser, returns ``InboundMessage`` or
  raises ``InboundError`` with a stable code.
- ``verify_signature(payload, header)``: HMAC-SHA256 verifier; constant-time
  comparison; raises ``InboundError`` on mismatch.
- ``match_voyage(message)``: best-effort match by the subject tag
  ``[V-12345]`` or by sender domain + recency window. Returns the
  ``voyage_id`` or ``None``.

What this module does NOT do
----------------------------

- Talk to SES. SES + the S3 bucket + the Lambda glue are deploy-time
  artifacts.
- Run ClamAV. The route trusts the Lambda's scan flag for v0.1; bringing
  AV in-process is a follow-up.
- Build any pipeline result. The route hands the parsed PDFs to the
  existing pipeline.run path so there is one canonical pipeline.

Dev harness
-----------

``scripts/dev_smtp_inbound.py`` (committed alongside) starts a tiny
``aiosmtpd`` server on localhost:1025 that signs and POSTs each received
message at ``/voyages/from-email`` so the full flow is testable on a laptop.
"""

from .models import (
    INBOUND_HMAC_HEADER,
    InboundAttachment,
    InboundError,
    InboundErrorCode,
    InboundMessage,
)
from .parser import parse_message
from .matcher import match_voyage
from .signature import sign_payload, verify_signature

__all__ = [
    "INBOUND_HMAC_HEADER",
    "InboundAttachment",
    "InboundError",
    "InboundErrorCode",
    "InboundMessage",
    "match_voyage",
    "parse_message",
    "sign_payload",
    "verify_signature",
]
