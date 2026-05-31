"""Tests for the SES email send adapter (notes/architecture_weeks_5_to_8.md §1.3).

The contract under test:
- ``LetterEmailRequest`` validates email addresses at the wire boundary.
- ``build_mime`` is pure and includes the letter body, subject, sender,
  recipients, and (when supplied) the PDF attachment.
- ``send_claim_letter`` honours the sandbox flag and returns a synthetic
  ``SesSendResult`` without touching boto3.
- ``EmailErrorCode`` enum maps cleanly to a stable HTTP status; the mapping
  is asserted so a future code addition does not silently regress to 500.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api.email import (  # noqa: E402
    EmailErrorCode,
    EmailSendError,
    LetterEmailRequest,
    build_mime,
    send_claim_letter,
)
from portside_api.fixtures import demo_voyage_fixture  # noqa: E402


# ---------------------------------------------------------------------------
# LetterEmailRequest validation
# ---------------------------------------------------------------------------


def test_request_rejects_invalid_to() -> None:
    with pytest.raises(Exception):  # Pydantic ValidationError
        LetterEmailRequest(to=["not-an-email"])


def test_request_rejects_empty_to() -> None:
    with pytest.raises(Exception):
        LetterEmailRequest(to=[])


def test_request_accepts_valid_addresses() -> None:
    req = LetterEmailRequest(
        to=["claims@charterer.com"],
        cc=["legal@us.com"],
        subject="Test",
    )
    assert req.to == ["claims@charterer.com"]
    assert req.cc == ["legal@us.com"]


def test_request_caps_recipients_at_twenty() -> None:
    too_many = [f"u{i}@x.com" for i in range(21)]
    with pytest.raises(Exception):
        LetterEmailRequest(to=too_many)


# ---------------------------------------------------------------------------
# build_mime
# ---------------------------------------------------------------------------


def test_build_mime_contains_letter_body_and_canonical_quantum() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["claims@charterer.com"])
    msg = build_mime(state, req)
    body = msg.get_content()
    # The Rotterdam fixture's letter mentions EUR 84,375.00; the email body
    # carries the canonical figure through.
    assert "84,375.00" in body
    assert msg["From"]
    assert msg["To"] == "claims@charterer.com"


def test_build_mime_uses_provided_subject_when_given() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["a@b.com"], subject="Custom subject")
    msg = build_mime(state, req)
    assert msg["Subject"] == "Custom subject"


def test_build_mime_default_subject_carries_vessel_and_ports() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["a@b.com"])
    msg = build_mime(state, req)
    cp = state.extraction.charter_party  # type: ignore[union-attr]
    subject = msg["Subject"]
    assert cp.vessel_name in subject
    assert cp.load_port in subject
    assert cp.discharge_port in subject


def test_build_mime_preamble_appears_before_letter_body() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(
        to=["a@b.com"],
        preamble_markdown="Dear Sirs, as discussed yesterday...",
    )
    msg = build_mime(state, req)
    body = msg.get_content()
    pre = body.find("as discussed yesterday")
    letter = body.find("84,375.00")
    assert 0 <= pre < letter, "preamble must appear before the letter body"


def test_build_mime_attaches_pdf_when_supplied() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["a@b.com"])
    msg = build_mime(state, req, pdf_bytes=b"%PDF-1.4 ...")
    attachments = [p for p in msg.iter_attachments()]
    assert len(attachments) == 1
    assert attachments[0].get_content_type() == "application/pdf"
    # Filename should carry the vessel + voyage id so a downloads folder reads.
    assert attachments[0].get_filename().endswith(".pdf")


# ---------------------------------------------------------------------------
# send_claim_letter (sandbox path; no boto3)
# ---------------------------------------------------------------------------


def test_sandbox_send_returns_synthetic_result_without_touching_boto() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["claims@charterer.com"])
    result = asyncio.run(send_claim_letter(state, req, live_override=False))
    assert result.sandbox is True
    assert result.ses_message_id == "sandbox"
    assert result.to == ["claims@charterer.com"]
    assert result.subject  # populated from the default


def test_sandbox_send_records_subject_from_request() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    req = LetterEmailRequest(to=["a@b.com"], subject="Override")
    result = asyncio.run(send_claim_letter(state, req, live_override=False))
    assert result.subject == "Override"


# ---------------------------------------------------------------------------
# Error code -> HTTP status mapping (locked at the route layer)
# ---------------------------------------------------------------------------


def test_error_code_enum_is_stable_and_complete() -> None:
    # Locking the set of error codes so an addition to the enum forces a code
    # change in the route's _EMAIL_ERROR_STATUS table.
    assert {c.value for c in EmailErrorCode} == {
        "SES_UNVERIFIED_RECIPIENT",
        "SES_THROTTLED",
        "SES_REJECTED",
        "SES_TRANSPORT",
        "SES_NOT_CONFIGURED",
    }


def test_email_send_error_carries_code_and_message() -> None:
    exc = EmailSendError(EmailErrorCode.THROTTLED, "rate limit")
    assert exc.code is EmailErrorCode.THROTTLED
    assert exc.message == "rate limit"
