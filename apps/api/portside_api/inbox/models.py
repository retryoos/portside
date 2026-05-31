"""Wire models for email-in ingestion."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


INBOUND_HMAC_HEADER = "X-Laytimely-Inbound-Signature"


class InboundErrorCode(str, Enum):
    BAD_SIGNATURE = "INBOUND_BAD_SIGNATURE"  # 401
    BAD_PAYLOAD = "INBOUND_BAD_PAYLOAD"  # 400
    NO_PDF_ATTACHMENT = "INBOUND_NO_PDF"  # 400
    OVERSIZE = "INBOUND_OVERSIZE"  # 413
    DISALLOWED_TYPE = "INBOUND_DISALLOWED_TYPE"  # 415
    VIRUS_DETECTED = "INBOUND_VIRUS"  # 422


class InboundError(RuntimeError):
    """Carry a stable code + a human message so the route can map to HTTP."""

    def __init__(self, code: InboundErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InboundAttachment(BaseModel):
    """One ``application/pdf`` attachment extracted from a forwarded message.

    Bytes never serialise; ``size_bytes`` is the audit-friendly summary. The
    raw bytes are carried alongside as a Python field so the route can hand
    them to the pipeline without re-parsing the MIME.
    """

    filename: str
    size_bytes: int
    # Excluded from JSON serialisation; the bytes belong inside the process,
    # not on the wire. The pipeline reads ``data`` directly.
    data: bytes = Field(repr=False, exclude=True)


class InboundMessage(BaseModel):
    """Parser output. Everything we need to decide what to do with the email."""

    sender: str
    recipients: list[str]
    subject: str
    voyage_tag: Optional[str] = None  # e.g. "v_abc123" extracted from "[V-abc123]"
    received_at: str  # ISO-8601 from the Date: header (or now() if missing)
    raw_size_bytes: int
    attachments: list[InboundAttachment]
    av_scanned: bool  # Lambda sets this; the route trusts it for v0.1
    av_clean: bool

    model_config = {"arbitrary_types_allowed": True}
