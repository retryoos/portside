"use client";

// Screen 3 Accept / Reject controls (DESIGN.md §Screens 3). Accept = ink primary
// (one per view); Reject = ghost/text in secondary. State is owned by ReviseLetter
// so the letter can reflect accepted/rejected; this is a presentational control.
export default function ReviseActions({
  onAccept,
  onReject,
}: {
  onAccept: () => void;
  onReject: () => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={onAccept}
        className="rounded-full bg-cta px-5 py-2.5 text-body-sm font-medium text-on-cta transition-colors hover:bg-cta-hover"
      >
        Accept revision
      </button>
      <button
        type="button"
        onClick={onReject}
        className="rounded-full px-4 py-2.5 text-body-sm font-medium text-secondary transition-colors hover:text-primary"
      >
        Reject
      </button>
    </div>
  );
}
