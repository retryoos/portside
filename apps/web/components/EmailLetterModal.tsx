"use client";

// Email-letter modal (W2, notes/architecture_weeks_5_to_8.md §1.3). Owned by
// EmailLetterButton via open state; mounted only when open so the form
// resets on each open. Hits POST /voyages/{id}/letter/email with the typed
// LetterEmailRequest body; surfaces backend EmailErrorCode in inline form
// errors so the customer can self-correct (THROTTLED -> retry; UNVERIFIED ->
// verify the address in SES; NOT_CONFIGURED -> tell admin).
//
// No portal library: we render a fixed-position overlay + card. Esc and a
// backdrop click both close; focus is moved to the To field on open.

import { useEffect, useId, useRef, useState } from "react";

import { sendClaimLetter } from "@/lib/api";
import type { EmailSendError, SesSendResult } from "@/lib/types";
import RecipientChipsInput from "@/components/RecipientChipsInput";

const ERROR_HINT: Record<string, string> = {
  SES_UNVERIFIED_RECIPIENT:
    "Recipient not verified in the SES sandbox. Verify the address in AWS first.",
  SES_THROTTLED: "SES is rate-limiting. Try again in a few seconds.",
  SES_REJECTED: "SES rejected the message. Check the recipients and subject.",
  SES_TRANSPORT: "Email transport failed. Try again; if it persists, ping ops.",
  SES_NOT_CONFIGURED:
    "Email not configured. An admin needs to add an SES identity.",
};

export default function EmailLetterModal({
  open,
  onClose,
  voyageId,
  defaultSubject,
  onSent,
}: {
  open: boolean;
  onClose: () => void;
  voyageId: string;
  defaultSubject: string;
  onSent: (result: SesSendResult) => void;
}) {
  const [to, setTo] = useState<string[]>([]);
  const [cc, setCc] = useState<string[]>([]);
  const [bcc, setBcc] = useState<string[]>([]);
  const [subject, setSubject] = useState(defaultSubject);
  const [preamble, setPreamble] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<EmailSendError | null>(null);

  const toId = useId();
  const ccId = useId();
  const bccId = useId();
  const subjectId = useId();
  const preambleId = useId();

  const cardRef = useRef<HTMLDivElement>(null);

  // Reset form on open so a previous draft never leaks into a new send.
  useEffect(() => {
    if (!open) return;
    setTo([]);
    setCc([]);
    setBcc([]);
    setSubject(defaultSubject);
    setPreamble("");
    setError(null);
    setBusy(false);
    // Focus the first input after the modal mounts.
    queueMicrotask(() => {
      document.getElementById(toId)?.focus();
    });
  }, [open, defaultSubject, toId]);

  // Esc closes the modal.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !busy) onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, busy]);

  if (!open) return null;

  async function handleSend() {
    if (busy) return;
    if (to.length === 0) {
      setError({ code: "UNKNOWN", message: "At least one recipient is required.", status: 0 });
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const result = await sendClaimLetter(voyageId, {
        to,
        cc,
        bcc,
        subject: subject.trim() || undefined,
        preamble_markdown: preamble.trim() || undefined,
      });
      onSent(result);
      onClose();
    } catch (e) {
      const sendError = e as EmailSendError;
      setError(sendError);
    } finally {
      setBusy(false);
    }
  }

  const errorMessage = error
    ? (ERROR_HINT[error.code] ?? error.message)
    : null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${subjectId}-title`}
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
    >
      <button
        type="button"
        aria-label="Close"
        onClick={() => (busy ? undefined : onClose())}
        className="absolute inset-0 bg-primary/30 backdrop-blur-sm"
      />
      <div
        ref={cardRef}
        className="relative w-full max-w-[560px] rounded-card border border-border bg-surface shadow-2xl"
      >
        <header className="flex items-start justify-between gap-4 border-b border-border px-7 pb-5 pt-6">
          <div>
            <p className="text-eyebrow text-secondary">Send via SES</p>
            <h2
              id={`${subjectId}-title`}
              className="mt-2 text-h3 text-primary"
            >
              Email claim letter
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            disabled={busy}
            className="-mr-2 -mt-1 flex h-9 w-9 items-center justify-center rounded-full text-secondary transition-colors hover:bg-surface-muted hover:text-primary disabled:opacity-50"
          >
            <svg
              aria-hidden
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              className="h-5 w-5"
            >
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </header>

        <div className="space-y-5 px-7 py-6">
          <RecipientChipsInput
            id={toId}
            label="To"
            values={to}
            onChange={setTo}
            required
            placeholder="claims@charterer.com"
          />
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            <RecipientChipsInput
              id={ccId}
              label="Cc"
              values={cc}
              onChange={setCc}
              placeholder="counsel@owner.com"
            />
            <RecipientChipsInput
              id={bccId}
              label="Bcc"
              values={bcc}
              onChange={setBcc}
              placeholder="archive@owner.com"
            />
          </div>

          <div>
            <label htmlFor={subjectId} className="text-eyebrow text-secondary">
              Subject
            </label>
            <input
              id={subjectId}
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={240}
              className="mt-2 w-full rounded-card border border-border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary"
            />
          </div>

          <div>
            <label htmlFor={preambleId} className="text-eyebrow text-secondary">
              Preamble (optional)
            </label>
            <textarea
              id={preambleId}
              value={preamble}
              onChange={(e) => setPreamble(e.target.value)}
              rows={3}
              maxLength={4000}
              placeholder="Short note prepended to the letter body."
              className="mt-2 w-full rounded-card border border-border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary"
            />
          </div>

          {errorMessage ? (
            <div
              role="alert"
              className="rounded-card border border-danger/20 bg-danger-container px-4 py-3 text-body-sm text-danger"
            >
              <p className="font-medium">{errorMessage}</p>
              {error && error.code !== "UNKNOWN" ? (
                <p className="mt-1 text-secondary">{error.message}</p>
              ) : null}
            </div>
          ) : null}
        </div>

        <footer className="flex items-center justify-end gap-3 border-t border-border px-7 py-5">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-pill px-4 py-2 text-body-sm text-secondary transition-colors hover:text-primary disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSend}
            disabled={busy || to.length === 0}
            className="btn-lift rounded-pill bg-cta px-5 py-2.5 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy ? "Sending…" : "Send letter"}
          </button>
        </footer>
      </div>
    </div>
  );
}
