"use client";

// /settings/inbox surface (W7, notes/architecture_weeks_5_to_8.md §2.3).
// Three parts:
//
//   1. The forward-to address (read-only, big, with a Copy button)
//   2. The privacy stance — Laytimely never reads the customer's mailbox;
//      the customer forwards what they want us to ingest.
//   3. Two short tutorials: Gmail filter -> forward, Outlook rule -> forward.
//      Plain numbered lists, no embedded screenshots; the steps are stable
//      and the screenshots rot.
//
// The copy button confirms via the same fixed-bottom-right toast pattern as
// EmailLetterButton: status="copied" rises, auto-dismisses in 3s, polite
// aria-live announces it for screen readers.

import { useEffect, useState } from "react";

const TOAST_TTL_MS = 3000;

export default function InboxSetupCard({
  address,
  loading = false,
}: {
  address: string | null;
  loading?: boolean;
}) {
  const [toast, setToast] = useState<"copied" | "failed" | null>(null);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), TOAST_TTL_MS);
    return () => clearTimeout(t);
  }, [toast]);

  async function handleCopy() {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      setToast("copied");
    } catch {
      setToast("failed");
    }
  }

  return (
    <div className="space-y-8">
      <AddressBlock address={address} loading={loading} onCopy={handleCopy} />
      <PrivacyNote />
      <TutorialsBlock address={address} />
      {toast ? <CopyToast status={toast} /> : null}
    </div>
  );
}

function AddressBlock({
  address,
  loading,
  onCopy,
}: {
  address: string | null;
  loading: boolean;
  onCopy: () => void;
}) {
  return (
    <section
      aria-label="Forward-to address"
      className="rounded-card border border-border bg-surface p-6"
    >
      <p className="text-eyebrow text-secondary">Forward-to address</p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        {loading ? (
          <div className="h-7 w-72 max-w-full rounded animate-shimmer" />
        ) : (
          <code
            data-testid="inbox-address"
            className="select-all break-all rounded-md bg-surface-muted px-3 py-2 font-mono text-h3 text-primary"
          >
            {address ?? "—"}
          </code>
        )}
        <button
          type="button"
          onClick={onCopy}
          disabled={!address || loading}
          className="inline-flex h-9 items-center gap-1.5 rounded-pill border border-border bg-surface px-4 text-body-sm font-semibold text-primary transition-colors hover:bg-surface-muted disabled:opacity-50"
          aria-label="Copy address"
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
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15V5a2 2 0 0 1 2-2h10" />
          </svg>
          Copy
        </button>
      </div>
      <p className="mt-4 text-body-sm text-secondary">
        Forward any email you want Laytimely to ingest to this address.
        Subject tags like <code className="font-mono text-primary">[V-abc123]</code>{" "}
        let us bind the forwarded message to a specific voyage.
      </p>
    </section>
  );
}

function PrivacyNote() {
  return (
    <section
      aria-label="Privacy stance"
      className="rounded-card border border-border bg-surface-muted p-6"
    >
      <p className="text-eyebrow text-secondary">Privacy</p>
      <p className="mt-3 text-body text-primary">
        Laytimely never connects to your mailbox. There is no OAuth, no
        IMAP read, no thread sync. You forward what you want us to see; we
        only ever process those messages.
      </p>
      <ul className="mt-4 space-y-2 text-body-sm text-secondary">
        <PrivacyItem>
          Inbound messages are HMAC-signed by our ingest hop; unsigned
          payloads are dropped fail-closed.
        </PrivacyItem>
        <PrivacyItem>
          Attachments are virus-scanned before they are persisted; non-PDF
          types are rejected.
        </PrivacyItem>
        <PrivacyItem>
          The forwarded message and its attachments retain the original
          sender headers so the audit log records who sent what.
        </PrivacyItem>
      </ul>
    </section>
  );
}

function PrivacyItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2">
      <span
        aria-hidden
        className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-secondary"
      />
      <span>{children}</span>
    </li>
  );
}

function TutorialsBlock({ address }: { address: string | null }) {
  return (
    <section
      aria-label="How to set up forwarding"
      className="grid gap-6 lg:grid-cols-2"
    >
      <TutorialCard
        title="Gmail filter"
        steps={[
          "Open Gmail → Settings → See all settings → Filters and Blocked Addresses.",
          "Click Create a new filter; in the From field, enter the address whose mail you want forwarded (e.g. the broker, the agent).",
          "Click Create filter, then tick Forward it to.",
          address
            ? `Pick this address from the dropdown: ${address}. If it is not listed yet, add it under Forwarding and POP/IMAP first.`
            : "Pick the Laytimely address from the dropdown. If it is not listed yet, add it under Forwarding and POP/IMAP first.",
          "Confirm Gmail's verification email; the filter goes live immediately.",
        ]}
      />
      <TutorialCard
        title="Outlook rule"
        steps={[
          "Open Outlook → Settings → Mail → Rules → Add new rule.",
          "Name the rule (e.g. \"Forward to Laytimely\").",
          "Condition: From → enter the address you want forwarded.",
          address
            ? `Action: Forward to → ${address}.`
            : "Action: Forward to → the Laytimely address shown above.",
          "Save. New matching messages will forward automatically; existing ones stay where they are.",
        ]}
      />
    </section>
  );
}

function TutorialCard({
  title,
  steps,
}: {
  title: string;
  steps: string[];
}) {
  return (
    <article className="rounded-card border border-border bg-surface p-6">
      <p className="text-eyebrow text-secondary">{title}</p>
      <ol className="mt-4 list-decimal space-y-2.5 pl-5 text-body-sm text-primary marker:text-secondary">
        {steps.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ol>
    </article>
  );
}

function CopyToast({ status }: { status: "copied" | "failed" }) {
  const positive = status === "copied";
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-6 right-6 z-50 rounded-card border border-border bg-surface px-4 py-3 shadow-lg"
    >
      <div className="flex items-center gap-2">
        <span
          aria-hidden
          className={`flex h-5 w-5 items-center justify-center rounded-full ${
            positive
              ? "bg-success-container text-success"
              : "bg-danger-container text-danger"
          }`}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3 w-3"
          >
            {positive ? (
              <path d="m5 12 4 4 10-10" />
            ) : (
              <path d="M6 6l12 12M18 6 6 18" />
            )}
          </svg>
        </span>
        <p className="text-body-sm font-semibold text-primary">
          {positive ? "Address copied" : "Copy failed — try selecting manually"}
        </p>
      </div>
    </div>
  );
}
