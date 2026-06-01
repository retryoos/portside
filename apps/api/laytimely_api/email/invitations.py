"""SES delivery of workspace invitations (review #12).

Mirrors the claim-letter SES adapter but small: invitations carry a short
plaintext body with the accept link. We deliberately keep the delivery
helper *separate* from ``send_claim_letter`` so a future templating swap
on either side does not collide.

Sandbox path (``settings.email_send_live=False`` or no SES identity) just
logs the send + returns a synthetic ``SesSendResult`` so dev environments
exercise the surface without an AWS dependency.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional

from ..settings import settings
from .models import (
    EmailErrorCode,
    EmailSendError,
    SesSendResult,
)

logger = logging.getLogger("laytimely_api.email.invitations")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_invitation_mime(
    *,
    recipient: str,
    sender: str,
    workspace_name: str,
    role: str,
    accept_url: str,
    invited_by_email: Optional[str] = None,
) -> EmailMessage:
    """Pure: build the MIME for a workspace invitation email.

    Plain text only (no HTML alternative) so the message reads cleanly in
    every client and there is no XSS surface from the workspace name.
    """
    msg = EmailMessage()
    msg["Subject"] = f"You're invited to {workspace_name} on Laytimely"
    msg["From"] = sender
    msg["To"] = recipient

    inviter_line = (
        f"{invited_by_email} added you" if invited_by_email else "You've been added"
    )
    msg.set_content(
        f"""\
{inviter_line} to the Laytimely workspace "{workspace_name}" as a {role}.

Accept the invitation:
{accept_url}

This link is good for 14 days. If you weren't expecting this email, you
can safely ignore it.

— Laytimely
"""
    )
    return msg


async def send_invitation_email(
    *,
    recipient: str,
    workspace_name: str,
    role: str,
    accept_url: str,
    invited_by_email: Optional[str] = None,
    live_override: Optional[bool] = None,
) -> SesSendResult:
    """Send the invitation email. Off-thread so the route does not block on
    SES. Honours the same ``settings.email_send_live`` flag as the claim
    letter path; in sandbox mode the call short-circuits to a synthetic
    success so dev environments still see a `workspace.invite` audit row
    with the right ``sandbox=true`` marker.
    """
    live = settings.email_send_live if live_override is None else live_override
    subject = f"You're invited to {workspace_name} on Laytimely"

    if not live:
        logger.info(
            "invitation-sandbox: to=%s workspace=%s role=%s",
            recipient,
            workspace_name,
            role,
        )
        return SesSendResult(
            ses_message_id="sandbox",
            sent_at=_now_iso(),
            to=[recipient],
            cc=[],
            bcc=[],
            subject=subject,
            sandbox=True,
        )

    sender = settings.ses_sender or "no-reply@laytimely.com"
    msg = build_invitation_mime(
        recipient=recipient,
        sender=sender,
        workspace_name=workspace_name,
        role=role,
        accept_url=accept_url,
        invited_by_email=invited_by_email,
    )
    return await asyncio.to_thread(_send_via_boto, msg, recipient, subject)


def _send_via_boto(
    message: EmailMessage, recipient: str, subject: str
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

    return SesSendResult(
        ses_message_id=response.get("MessageId") or "",
        sent_at=_now_iso(),
        to=[recipient],
        cc=[],
        bcc=[],
        subject=subject,
        sandbox=False,
    )
