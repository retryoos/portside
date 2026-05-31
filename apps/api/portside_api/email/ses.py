"""SES send adapter for the claim packet (notes/architecture_weeks_5_to_8.md §1.3).

The boto3 client is imported lazily so dev environments without AWS creds can
still run the test suite. ``settings.email_send_live`` gates the real call:
when off, ``send_claim_letter`` records the attempt and returns a synthetic
``SesSendResult`` so the route, the audit log, and the rate limiter still get
exercised end-to-end.

Error taxonomy
--------------

``EmailSendError`` carries a stable ``EmailErrorCode`` enum the route handler
maps to an HTTP status (sandbox 422, throttling 429, transport 502). String
matching on boto3 exception messages is intentionally kept to the smallest
surface needed for that mapping; SES exceptions are otherwise allowed to
bubble.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import TYPE_CHECKING, Optional

from ..schemas import VoyageState
from ..settings import settings
from .models import (
    EmailErrorCode,
    EmailSendError,
    LetterEmailRequest,
    SesSendResult,
)

if TYPE_CHECKING:
    # boto3 typing stubs are not pinned; this hint exists for editors only.
    from botocore.exceptions import ClientError  # noqa: F401  # pragma: no cover

logger = logging.getLogger("portside_api.email.ses")

# Default sender address. Production swaps via env (`SES_SENDER`).
_DEFAULT_SENDER = "claims@laytimely.com"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_subject(state: VoyageState) -> str:
    cp = state.extraction.charter_party if state.extraction else None
    if cp:
        return (
            f"Demurrage Claim, {cp.vessel_name}, "
            f"{cp.load_port} / {cp.discharge_port}, CP dated {cp.cp_date}"
        )
    return f"Demurrage Claim, voyage {state.voyage_id}"


def build_mime(
    state: VoyageState,
    request: LetterEmailRequest,
    pdf_bytes: Optional[bytes] = None,
    sender: str = _DEFAULT_SENDER,
) -> EmailMessage:
    """Render the RFC 822 message. Pure function (no I/O) so it is testable.

    Body is the letter Markdown plus the optional ``preamble_markdown`` on top.
    Real production wiring later sends an HTML alternative too; v0.1 is plain
    text, which lawyers prefer for redlining.
    """
    subject = (request.subject or _default_subject(state)).strip()
    body_parts: list[str] = []
    if request.preamble_markdown:
        body_parts.append(request.preamble_markdown.strip())
    if state.packet and state.packet.claim_letter_markdown:
        body_parts.append(state.packet.claim_letter_markdown.strip())
    body_parts.append(
        "\n--\nSent via Laytimely — https://laytimely.com\n"
        "Reply to this email or contact claims@laytimely.com."
    )
    text_body = "\n\n".join(b for b in body_parts if b)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(request.to)
    if request.cc:
        msg["Cc"] = ", ".join(request.cc)
    if request.bcc:
        msg["Bcc"] = ", ".join(request.bcc)
    msg.set_content(text_body)

    if pdf_bytes:
        vessel = (
            state.extraction.charter_party.vessel_name.replace(" ", "_")
            if state.extraction
            else "voyage"
        )
        filename = f"demurrage-claim-{vessel}-{state.voyage_id}.pdf"
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )
    return msg


async def send_claim_letter(
    state: VoyageState,
    request: LetterEmailRequest,
    pdf_bytes: Optional[bytes] = None,
    *,
    live_override: Optional[bool] = None,
) -> SesSendResult:
    """Send the claim letter. Off-thread so the event loop never blocks on a
    multi-MB attachment.

    ``live_override`` short-circuits the settings flag for tests so we can
    exercise the sandbox path and the live error mapping without changing env
    vars between runs.
    """
    live = settings.email_send_live if live_override is None else live_override
    subject = (request.subject or _default_subject(state)).strip()

    if not live:
        logger.info(
            "email-sandbox: voyage=%s to=%s cc=%s",
            state.voyage_id,
            request.to,
            request.cc,
        )
        return SesSendResult(
            ses_message_id="sandbox",
            sent_at=_now_iso(),
            to=list(request.to),
            cc=list(request.cc),
            bcc=list(request.bcc),
            subject=subject,
            sandbox=True,
        )

    message = build_mime(state, request, pdf_bytes)
    return await asyncio.to_thread(_send_via_boto, message, request, subject)


def _send_via_boto(
    message: EmailMessage, request: LetterEmailRequest, subject: str
) -> SesSendResult:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:  # pragma: no cover - boto3 in deps
        raise EmailSendError(EmailErrorCode.NOT_CONFIGURED, str(exc)) from exc

    client = boto3.client("ses", region_name=settings.s3_region or "eu-central-1")
    raw = message.as_bytes()

    try:
        response = client.send_raw_email(RawMessage={"Data": raw})
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        msg = exc.response.get("Error", {}).get("Message", str(exc))
        if code == "MessageRejected" and "not verified" in msg.lower():
            raise EmailSendError(EmailErrorCode.SANDBOX_UNVERIFIED, msg) from exc
        if code == "Throttling":
            raise EmailSendError(EmailErrorCode.THROTTLED, msg) from exc
        if code == "MessageRejected":
            raise EmailSendError(EmailErrorCode.REJECTED, msg) from exc
        raise EmailSendError(EmailErrorCode.TRANSPORT, msg) from exc
    except BotoCoreError as exc:  # network etc.
        raise EmailSendError(EmailErrorCode.TRANSPORT, str(exc)) from exc

    message_id = response.get("MessageId") or ""
    return SesSendResult(
        ses_message_id=message_id,
        sent_at=_now_iso(),
        to=list(request.to),
        cc=list(request.cc),
        bcc=list(request.bcc),
        subject=subject,
        sandbox=False,
    )
