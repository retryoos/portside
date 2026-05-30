"use client";

// Inline revise Accept / Reject controls. Accept = ink primary (one per
// view); Reject = ghost-text in secondary. State lives in ReviseLetter so the
// letter reflects accepted/rejected; this is a presentational control.
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
        className="btn-lift rounded-pill bg-cta px-5 py-2.5 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
      >
        Accept revision
      </button>
      <button
        type="button"
        onClick={onReject}
        className="rounded-pill px-4 py-2.5 text-body-sm font-semibold text-secondary transition-colors hover:text-primary"
      >
        Reject
      </button>
    </div>
  );
}
