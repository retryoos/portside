"""HMAC-SHA256 verification for the inbound email boundary.

The Lambda computes ``sign_payload(secret, raw_eml_bytes)`` and passes the
hex digest in ``INBOUND_HMAC_HEADER``; the route verifies in constant time
and raises ``InboundError(BAD_SIGNATURE)`` on mismatch. The secret is
``settings.email_in_shared_secret``; when unset, the route refuses inbound
calls so a forgotten env var fails closed.
"""

from __future__ import annotations

import hashlib
import hmac

from .models import InboundError, InboundErrorCode


def sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_signature(
    secret: str | None,
    payload: bytes,
    header_value: str | None,
) -> None:
    """Raise ``InboundError`` on any failure; return None on success.

    Fails closed: a missing secret rejects every inbound call.
    """
    if not secret:
        raise InboundError(
            InboundErrorCode.BAD_SIGNATURE,
            "inbound boundary not configured: missing EMAIL_IN_SHARED_SECRET",
        )
    if not header_value:
        raise InboundError(InboundErrorCode.BAD_SIGNATURE, "missing signature header")
    expected = sign_payload(secret, payload)
    if not hmac.compare_digest(expected, header_value.strip()):
        raise InboundError(InboundErrorCode.BAD_SIGNATURE, "signature mismatch")
