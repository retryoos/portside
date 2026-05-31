"use client";

// Primary CTA pill that opens the EmailLetterModal. Owns the modal open state
// and the success toast so the case-detail page does not need a toast
// context for one feature. The toast auto-dismisses after 5s; it surfaces
// either "Sent (sandbox)" or "Sent (message <prefix>)" depending on whether
// the backend ran in sandbox or live SES mode.

import { useEffect, useState } from "react";

import EmailLetterModal from "@/components/EmailLetterModal";
import type { SesSendResult } from "@/lib/types";

const TOAST_TTL_MS = 5000;

export default function EmailLetterButton({
  voyageId,
  vesselName,
}: {
  voyageId: string;
  vesselName?: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [toast, setToast] = useState<SesSendResult | null>(null);

  // Auto-dismiss the toast after a few seconds.
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), TOAST_TTL_MS);
    return () => clearTimeout(t);
  }, [toast]);

  const defaultSubject = vesselName
    ? `Demurrage Claim — ${vesselName} (${voyageId})`
    : `Demurrage Claim — ${voyageId}`;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Email claim letter"
        title="Email claim letter"
        className="btn-lift inline-flex h-9 items-center gap-1.5 rounded-pill bg-cta px-4 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
      >
        <svg
          aria-hidden
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
        >
          <path d="m3 7 9 6 9-6" />
          <rect x="3" y="5" width="18" height="14" rx="2" />
        </svg>
        Email letter
      </button>

      <EmailLetterModal
        open={open}
        onClose={() => setOpen(false)}
        voyageId={voyageId}
        defaultSubject={defaultSubject}
        onSent={setToast}
      />

      {toast ? <SendToast result={toast} onDismiss={() => setToast(null)} /> : null}
    </>
  );
}

function SendToast({
  result,
  onDismiss,
}: {
  result: SesSendResult;
  onDismiss: () => void;
}) {
  const summary = result.sandbox
    ? "Sent (sandbox)"
    : `Sent (message ${result.ses_message_id.slice(0, 12)}…)`;
  const recipientCount = result.to.length + result.cc.length + result.bcc.length;
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-6 right-6 z-50 max-w-sm rounded-card border border-border bg-surface px-5 py-4 shadow-lg"
    >
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success-container text-success"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5"
          >
            <path d="m5 12 4 4 10-10" />
          </svg>
        </span>
        <div className="flex-1">
          <p className="text-body-sm font-semibold text-primary">{summary}</p>
          <p className="mt-0.5 text-body-sm text-secondary">
            {recipientCount} recipient{recipientCount === 1 ? "" : "s"}
          </p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          className="-mr-1 -mt-1 flex h-6 w-6 items-center justify-center rounded-full text-secondary hover:bg-surface-muted hover:text-primary"
        >
          <svg
            aria-hidden
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            className="h-3.5 w-3.5"
          >
            <path d="M6 6l12 12M18 6 6 18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
