"use client";

import { useState } from "react";
import RevisePrompt from "@/components/RevisePrompt";
import ReviseActions from "@/components/ReviseActions";

// Inline highlight-and-revise (DESIGN.md "Surfaces"). Self-contained CLIENT MOCK,
// no backend revise endpoint. Renders the formal letter with ONE target sentence
// (the weather argument). The replacement sits in a white card with a hairline
// ink border (no amber tint). Accept / Reject toggles which version is live.

const ORIGINAL_SENTENCE =
  "The charterer claims a 4-hour weather stoppage on 17 May 2026; we consider that this time should count.";

const REPLACEMENT_PARAGRAPH =
  "The charterer's claim of a 4-hour weather stoppage on 17 May 2026 cannot be sustained. CP clause 14 excepts weather from laytime only where precipitation at the place of discharge exceeds 0.5 mm per hour. The Rotterdam Port Authority precipitation data records a maximum of 0.2 mm/hr on 17 May 2026, below the 0.5 mm/hr threshold, so the contractual condition is not met. As confirmed in The Mexico 1 [1990] 1 Lloyd's Rep 507, a stoppage must satisfy the express contractual condition before it may be deducted from laytime; the 4-hour period therefore counts in full.";

const PROMPT_DEFAULT =
  "Make the weather argument stronger and cite The Mexico 1";

type RevisionState = "pending" | "accepted" | "rejected";

export default function ReviseLetter() {
  const [state, setState] = useState<RevisionState>("pending");

  return (
    <article className="rounded-card border border-border bg-surface px-8 py-10 text-letter-body text-primary md:px-14 md:py-14">
      <p className="text-eyebrow text-secondary">To: Charterers</p>

      <p className="mt-10">Dear Sirs,</p>

      <p className="mt-4 font-semibold">
        Re: Demurrage Claim, MT Aegean Pioneer, Ras Tanura / Rotterdam, CP dated
        12 February 2026
      </p>

      <p className="mt-4">
        We write further to the captioned charter party in respect of the
        discharge port call at Rotterdam, completed on 19 May 2026. The total
        laytime used exceeded the agreed allowance of 72 hours by 45 hours,
        placing the vessel on demurrage.
      </p>

      {/* The single revisable sentence. */}
      {state === "rejected" ? (
        <p className="mt-4">{ORIGINAL_SENTENCE}</p>
      ) : state === "accepted" ? (
        <p className="mt-4">{REPLACEMENT_PARAGRAPH}</p>
      ) : (
        <div className="mt-4">
          <p className="text-secondary line-through">{ORIGINAL_SENTENCE}</p>
          <div className="mt-4 rounded-md border border-border-strong bg-surface p-5">
            <p className="text-eyebrow text-secondary">Suggested revision</p>
            <p className="mt-3 text-primary">{REPLACEMENT_PARAGRAPH}</p>
          </div>
        </div>
      )}

      <p className="mt-4">
        We accordingly demand payment of EUR 84,375.00 within 30 days of the date
        of this letter. All rights reserved.
      </p>

      <p className="mt-6">
        Yours faithfully,
        <br />
        For and on behalf of Aegean Tankers S.A.
      </p>

      {/* Floating quick-prompt + accept/reject, only while a revision is pending. */}
      {state === "pending" && (
        <div className="card-glass sticky bottom-6 mt-12 px-5 py-5">
          <RevisePrompt defaultValue={PROMPT_DEFAULT} />
          <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
            <p className="text-body-sm text-secondary">
              The agent rewrote one sentence. Quantum and citations are
              preserved.
            </p>
            <ReviseActions
              onAccept={() => setState("accepted")}
              onReject={() => setState("rejected")}
            />
          </div>
        </div>
      )}

      {state !== "pending" && (
        <div className="mt-12 flex items-center justify-between gap-4 rounded-md border border-border bg-surface-muted px-5 py-4">
          <p className="text-body-sm text-secondary">
            {state === "accepted"
              ? "Revision accepted. The letter now uses the strengthened weather argument."
              : "Revision rejected. The original sentence is retained."}
          </p>
          <button
            type="button"
            onClick={() => setState("pending")}
            className="rounded-pill px-4 py-2 text-body-sm font-semibold text-secondary transition-colors hover:text-primary"
          >
            Undo
          </button>
        </div>
      )}
    </article>
  );
}
