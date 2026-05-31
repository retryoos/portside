"""RFC 822 parser for inbound email (notes/architecture_weeks_5_to_8.md §2.3).

Pure: input is the raw bytes of the message, output is an ``InboundMessage``
(or an ``InboundError`` with a stable code). Stdlib ``email.parser`` does
the heavy lifting; we just enforce the policy:

- At least one ``application/pdf`` attachment.
- No archives, no Office macros, no scripts (``.docm``, ``.xlsm``, ``.zip``,
  ``.rar`` — defence in depth alongside SES rules).
- 25 MB cap per message and 25 MB cap per attachment (SES already rejects
  larger; the cap here protects us if the boundary is swapped).
- AV scan flag from the Lambda is required and must be ``clean``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from typing import Optional

from .models import (
    InboundAttachment,
    InboundError,
    InboundErrorCode,
    InboundMessage,
)

# 25 MB. Mirror SES default and the upload limits in portside_api/limits.py.
_MAX_MESSAGE_BYTES = 25 * 1024 * 1024
_MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

# Filenames that we drop regardless of the declared content-type. Defence in
# depth: SES + S3 + the Lambda VirusTotal scan all run first; this is the
# floor.
_DROP_EXTENSIONS = (".docm", ".xlsm", ".pptm", ".js", ".exe", ".zip", ".rar", ".7z")

# Subject tag we look for to match an existing voyage. Format
# ``[V-<voyage_id>]`` so the user can include the tag verbatim from the case
# detail URL ("v_abc123def"). Case-insensitive.
_VOYAGE_TAG_RE = re.compile(r"\[v[-_]([0-9a-z]{4,32})\]", re.IGNORECASE)


def parse_message(
    raw: bytes,
    *,
    av_scanned: bool,
    av_clean: bool,
) -> InboundMessage:
    """Parse a raw RFC 822 message. Pure; never touches network or storage.

    The two AV flags are passed in by the route layer (which reads them from
    HTTP headers the Lambda sets). We do not run an in-process scanner; the
    Lambda is the canonical scanner today.
    """
    if not av_scanned or not av_clean:
        raise InboundError(
            InboundErrorCode.VIRUS_DETECTED,
            "rejected: message has not passed AV scan",
        )
    if len(raw) > _MAX_MESSAGE_BYTES:
        raise InboundError(
            InboundErrorCode.OVERSIZE,
            f"message size {len(raw)} bytes exceeds {_MAX_MESSAGE_BYTES}",
        )

    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:  # noqa: BLE001 - boundary handler
        raise InboundError(
            InboundErrorCode.BAD_PAYLOAD, f"unparseable message: {exc}"
        ) from exc

    sender = _first_address(msg.get("From", ""))
    if not sender:
        raise InboundError(InboundErrorCode.BAD_PAYLOAD, "missing From: header")

    to_field = ", ".join(filter(None, [msg.get("To", ""), msg.get("Cc", "")]))
    recipients = [addr for _name, addr in getaddresses([to_field]) if addr]

    subject = (msg.get("Subject") or "").strip()
    voyage_tag = _extract_voyage_tag(subject)

    received_at = _parse_date(msg.get("Date"))

    attachments = _extract_pdf_attachments(msg)
    if not attachments:
        raise InboundError(
            InboundErrorCode.NO_PDF_ATTACHMENT,
            "no application/pdf attachment present",
        )

    return InboundMessage(
        sender=sender,
        recipients=recipients,
        subject=subject,
        voyage_tag=voyage_tag,
        received_at=received_at,
        raw_size_bytes=len(raw),
        attachments=attachments,
        av_scanned=av_scanned,
        av_clean=av_clean,
    )


def _first_address(value: str) -> Optional[str]:
    pairs = getaddresses([value])
    for _name, addr in pairs:
        if addr:
            return addr
    return None


def _extract_voyage_tag(subject: str) -> Optional[str]:
    m = _VOYAGE_TAG_RE.search(subject)
    return f"v_{m.group(1).lower()}" if m else None


def _parse_date(value: Optional[str]) -> str:
    if value:
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _extract_pdf_attachments(msg) -> list[InboundAttachment]:
    out: list[InboundAttachment] = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        filename = (part.get_filename() or "").strip()
        if filename and filename.lower().endswith(_DROP_EXTENSIONS):
            raise InboundError(
                InboundErrorCode.DISALLOWED_TYPE,
                f"disallowed attachment extension: {filename}",
            )
        ctype = (part.get_content_type() or "").lower()
        if ctype != "application/pdf":
            continue
        data = part.get_payload(decode=True) or b""
        if len(data) == 0:
            continue
        if len(data) > _MAX_ATTACHMENT_BYTES:
            raise InboundError(
                InboundErrorCode.OVERSIZE,
                f"attachment {filename or '?'} exceeds {_MAX_ATTACHMENT_BYTES}",
            )
        out.append(
            InboundAttachment(
                filename=filename or "attachment.pdf",
                size_bytes=len(data),
                data=data,
            )
        )
    return out
