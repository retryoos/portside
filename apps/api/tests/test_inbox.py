"""Tests for email-in ingestion (notes/architecture_weeks_5_to_8.md §2.3).

Four blocks:

- ``verify_signature`` rejects empty/wrong sigs in constant time; fails
  closed on a missing secret.
- ``parse_message`` extracts sender, subject, voyage tag, attachments;
  rejects oversize and disallowed types.
- ``match_voyage`` returns the tagged id when present, None otherwise.
- A round-trip: sign a fixture message, verify, parse, and match.
"""

from __future__ import annotations

import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api.inbox import (  # noqa: E402
    InboundError,
    InboundErrorCode,
    InboundMessage,
    match_voyage,
    parse_message,
    sign_payload,
    verify_signature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_email(
    *,
    sender: str = "ops@charterer.com",
    to: str = "in+v_abc123@in.laytimely.com",
    subject: str = "Voyage docs",
    pdf_bytes: bytes = b"%PDF-1.4 test",
    pdf_filename: str = "cp.pdf",
    extras: list[tuple[bytes, str, str]] | None = None,
) -> bytes:
    """Build an RFC 822 multipart message with at least one PDF attachment."""
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = "Sat, 31 May 2026 09:00:00 +0000"
    msg.attach(MIMEText("Please find attached.\n", "plain"))

    def _attach(data: bytes, filename: str, ctype: str) -> None:
        sub = ctype.split("/", 1)[1] if "/" in ctype else "octet-stream"
        part = MIMEApplication(data, _subtype=sub)
        part.add_header("Content-Disposition", "attachment", filename=filename)
        # MIMEApplication sets application/<sub> automatically, but allow
        # overrides for the disallowed-type tests.
        if "application/" not in ctype:
            part.set_type(ctype)
        msg.attach(part)

    _attach(pdf_bytes, pdf_filename, "application/pdf")
    for data, filename, ctype in extras or []:
        _attach(data, filename, ctype)
    return msg.as_bytes()


# ---------------------------------------------------------------------------
# verify_signature
# ---------------------------------------------------------------------------


def test_verify_signature_accepts_matching_digest() -> None:
    secret = "topsecret"
    payload = b"hello"
    sig = sign_payload(secret, payload)
    verify_signature(secret, payload, sig)  # no raise


def test_verify_signature_rejects_wrong_digest() -> None:
    with pytest.raises(InboundError) as exc:
        verify_signature("topsecret", b"hello", "deadbeef")
    assert exc.value.code is InboundErrorCode.BAD_SIGNATURE


def test_verify_signature_fails_closed_on_missing_secret() -> None:
    with pytest.raises(InboundError) as exc:
        verify_signature(None, b"hello", "anything")
    assert exc.value.code is InboundErrorCode.BAD_SIGNATURE


def test_verify_signature_rejects_missing_header() -> None:
    with pytest.raises(InboundError) as exc:
        verify_signature("topsecret", b"hello", None)
    assert exc.value.code is InboundErrorCode.BAD_SIGNATURE


# ---------------------------------------------------------------------------
# parse_message
# ---------------------------------------------------------------------------


def _parse(raw: bytes) -> InboundMessage:
    return parse_message(raw, av_scanned=True, av_clean=True)


def test_parse_extracts_sender_recipients_subject_attachments() -> None:
    raw = _build_email()
    msg = _parse(raw)
    assert msg.sender == "ops@charterer.com"
    assert msg.recipients == ["in+v_abc123@in.laytimely.com"]
    assert msg.subject == "Voyage docs"
    assert len(msg.attachments) == 1
    assert msg.attachments[0].filename == "cp.pdf"
    assert msg.attachments[0].size_bytes == len(b"%PDF-1.4 test")


def test_parse_pulls_voyage_tag_from_subject() -> None:
    raw = _build_email(subject="Re: [V-abc123def] More docs")
    msg = _parse(raw)
    assert msg.voyage_tag == "v_abc123def"


def test_parse_rejects_when_av_not_clean() -> None:
    raw = _build_email()
    with pytest.raises(InboundError) as exc:
        parse_message(raw, av_scanned=True, av_clean=False)
    assert exc.value.code is InboundErrorCode.VIRUS_DETECTED


def test_parse_rejects_when_av_not_scanned() -> None:
    raw = _build_email()
    with pytest.raises(InboundError) as exc:
        parse_message(raw, av_scanned=False, av_clean=True)
    assert exc.value.code is InboundErrorCode.VIRUS_DETECTED


def test_parse_rejects_no_pdf_attachment() -> None:
    # A message with only a text part.
    msg = MIMEText("just text", "plain")
    msg["From"] = "ops@charterer.com"
    msg["To"] = "in@in.laytimely.com"
    msg["Subject"] = "no pdf"
    with pytest.raises(InboundError) as exc:
        _parse(msg.as_bytes())
    assert exc.value.code is InboundErrorCode.NO_PDF_ATTACHMENT


def test_parse_rejects_disallowed_extension() -> None:
    raw = _build_email(
        extras=[(b"x", "macro.docm", "application/vnd.ms-word.document.macroEnabled.12")]
    )
    with pytest.raises(InboundError) as exc:
        _parse(raw)
    assert exc.value.code is InboundErrorCode.DISALLOWED_TYPE


def test_parse_rejects_missing_from_header() -> None:
    msg = MIMEMultipart()
    msg["To"] = "in@in.laytimely.com"
    msg["Subject"] = "x"
    part = MIMEApplication(b"%PDF", _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename="x.pdf")
    msg.attach(part)
    with pytest.raises(InboundError) as exc:
        _parse(msg.as_bytes())
    assert exc.value.code is InboundErrorCode.BAD_PAYLOAD


# ---------------------------------------------------------------------------
# match_voyage
# ---------------------------------------------------------------------------


def test_match_voyage_returns_tag_when_present() -> None:
    raw = _build_email(subject="Re: [V-abc123def] more docs")
    msg = _parse(raw)
    assert match_voyage(msg) == "v_abc123def"


def test_match_voyage_returns_none_when_no_tag() -> None:
    raw = _build_email(subject="No tag here")
    msg = _parse(raw)
    assert match_voyage(msg) is None


# ---------------------------------------------------------------------------
# End-to-end: sign -> verify -> parse -> match
# ---------------------------------------------------------------------------


def test_end_to_end_sign_verify_parse_match() -> None:
    raw = _build_email(subject="[V-abc123def] docs")
    sig = sign_payload("topsecret", raw)
    verify_signature("topsecret", raw, sig)
    msg = _parse(raw)
    assert match_voyage(msg) == "v_abc123def"
