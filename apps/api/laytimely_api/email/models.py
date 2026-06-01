"""Wire models for the email subsystem (notes/architecture_weeks_5_to_8.md §1.3)."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# A pragmatic RFC 5322 subset. Good enough for v0.1; SES will do the strict
# pass and reject anything malformed at submission.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LetterEmailRequest(BaseModel):
    """Body for ``POST /voyages/{id}/letter/email``.

    The PDF attachment is uploaded by the route handler as a multipart file
    field alongside this JSON body, so this model does not carry the bytes.
    Keeping them out of the wire model also keeps Pydantic from materialising
    a megabyte of base64 on every request.
    """

    to: list[str] = Field(..., min_length=1, max_length=20)
    cc: list[str] = Field(default_factory=list, max_length=20)
    bcc: list[str] = Field(default_factory=list, max_length=20)
    subject: Optional[str] = Field(None, max_length=240)
    preamble_markdown: Optional[str] = Field(None, max_length=4000)

    @field_validator("to", "cc", "bcc")
    @classmethod
    def _validate_emails(cls, addrs: list[str]) -> list[str]:
        for addr in addrs:
            if not _EMAIL_RE.match(addr):
                raise ValueError(f"invalid email address: {addr!r}")
        return addrs


class EmailErrorCode(str, Enum):
    """Stable enum the route handler maps to an HTTP status."""

    SANDBOX_UNVERIFIED = "SES_UNVERIFIED_RECIPIENT"  # 422
    THROTTLED = "SES_THROTTLED"  # 429
    REJECTED = "SES_REJECTED"  # 422
    TRANSPORT = "SES_TRANSPORT"  # 502
    NOT_CONFIGURED = "SES_NOT_CONFIGURED"  # 503


class EmailSendError(RuntimeError):
    """Carry a stable code + a human message so the route handler can map to
    the right HTTP status without inspecting strings."""

    def __init__(self, code: EmailErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SesSendResult(BaseModel):
    ses_message_id: str
    sent_at: str  # ISO-8601 timestamp from time-of-send
    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    sandbox: bool  # True when settings.email_send_live was off
