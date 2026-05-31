"use client";

// Mailto fallback for the claim letter (notes/architecture_weeks_5_to_8.md
// §1.3 follow-up). Opens the customer's default mail client with the letter
// pre-filled as plain text in the body and a templated subject line. Sits
// next to the SES "Email letter" button; the right choice when SES
// production access has not landed yet, or when the customer wants the
// outgoing message in their OWN Sent folder for their OWN audit trail.
//
// mailto: does NOT support attachments. The customer keeps the downloaded
// PDF/Word from the adjacent export buttons and drags them in. Most clients
// fold the body at 998 chars per line per RFC 5322; we replace markdown
// emphasis with plain syntax and truncate at 30k chars to stay under the
// mailto: URL size most browsers accept (~2MB on Chrome; safer 8k cap).

const BODY_CHAR_CAP = 8000;

export default function MailtoLetterButton({
  letterMarkdown,
  vesselName,
  voyageId,
  to,
}: {
  letterMarkdown: string;
  vesselName?: string | null;
  voyageId: string;
  to?: string;
}) {
  function handleOpen() {
    const subject = vesselName
      ? `Demurrage Claim — ${vesselName} (${voyageId})`
      : `Demurrage Claim — ${voyageId}`;
    const body = prepareBody(letterMarkdown);
    const params = new URLSearchParams();
    params.set("subject", subject);
    params.set("body", body);
    const href = `mailto:${to ?? ""}?${params.toString()}`;
    // Use a temporary anchor instead of window.location so the user's
    // default mail handler is invoked even when the route was rendered in
    // an iframe (some shipping ops teams view the app inside a parent
    // shell).
    const a = document.createElement("a");
    a.href = href;
    a.rel = "noopener";
    a.click();
  }

  return (
    <button
      type="button"
      onClick={handleOpen}
      aria-label="Open in your email client"
      title="Open in your email client"
      className="flex h-9 w-9 items-center justify-center rounded-full text-primary transition-colors hover:bg-surface-muted"
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 7 9 6 9-6" />
      </svg>
    </button>
  );
}

/**
 * Strip markdown syntax that hurts plain-text email readers; truncate to
 * the body cap so the mailto: URL is acceptable to common mail clients.
 *
 * Pure function so a unit test can lock the exact transformations.
 */
export function prepareBody(markdown: string): string {
  const stripped = markdown
    // Bold + italic markers: drop the asterisks/underscores entirely.
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    // Inline code backticks.
    .replace(/`([^`]+)`/g, "$1")
    // Heading markers become a leading "## " stripped down to plain caps line.
    .replace(/^#{1,6}\s+(.+)$/gm, "$1")
    // Links: keep the visible text, drop the URL.
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)")
    // List bullets become a hyphen prefix; preserves indentation.
    .replace(/^(\s*)[-*+]\s+/gm, "$1- ");

  if (stripped.length <= BODY_CHAR_CAP) return stripped;
  return (
    stripped.slice(0, BODY_CHAR_CAP) +
    "\n\n[Letter truncated for email body; full letter attached as PDF.]"
  );
}
