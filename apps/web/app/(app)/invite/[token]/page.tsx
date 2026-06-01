"use client";

// SCREEN: /invite/<token> (W9, notes/architecture_weeks_5_to_8.md §2.1).
// Public-ish accept page: any authed user can land here and accept the
// invitation, even if they are not yet a member of any workspace. The
// middleware redirects unauthed visitors to /login?next=/invite/<token>;
// after sign-in they bounce back and the page mounts as below.
//
// UX is a single editorial card with three states:
//   - idle: "Join <workspace>" + Accept CTA + role chip
//   - busy: spinner-equivalent ("Joining...")
//   - settled: success ("You are in. Redirecting to /cases.") OR error
//     (410 expired/revoked, 404 unknown token, etc.) with a "Back to
//     cases" link as a safe out.

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import TopNav from "@/components/TopNav";
import { acceptInvitation } from "@/lib/api";
import type {
  WorkspaceError,
  WorkspaceInvitation,
  WorkspaceRole,
} from "@/lib/types";

const ROLE_TONE: Record<WorkspaceRole, string> = {
  owner: "bg-primary text-on-primary",
  admin: "bg-success-container text-success",
  member: "bg-surface-muted text-primary",
};

type Status = "idle" | "busy" | "success" | "error";

export default function InviteAcceptPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const router = useRouter();
  const [status, setStatus] = useState<Status>("idle");
  const [accepted, setAccepted] = useState<WorkspaceInvitation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAccept = useCallback(async () => {
    if (status === "busy" || status === "success") return;
    setStatus("busy");
    setError(null);
    try {
      const invite = await acceptInvitation(token);
      setAccepted(invite);
      setStatus("success");
    } catch (e) {
      const err = e as WorkspaceError;
      setError(invitationErrorMessage(err));
      setStatus("error");
    }
  }, [token, status]);

  // Auto-redirect to the cases dashboard a moment after success so the
  // user lands somewhere actionable.
  useEffect(() => {
    if (status !== "success") return;
    const t = setTimeout(() => router.replace("/cases"), 1500);
    return () => clearTimeout(t);
  }, [status, router]);

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[640px] px-6 pb-24 pt-12 md:px-8 md:pt-20">
        <article className="rounded-card border border-border bg-surface p-8 md:p-12">
          <p className="text-eyebrow text-secondary">Workspace invitation</p>
          {status === "success" && accepted ? (
            <SuccessBlock invite={accepted} />
          ) : status === "error" ? (
            <ErrorBlock message={error ?? "Could not accept invitation."} />
          ) : (
            <IdleBlock onAccept={handleAccept} busy={status === "busy"} />
          )}
        </article>
      </main>
    </div>
  );
}

function IdleBlock({
  onAccept,
  busy,
}: {
  onAccept: () => void;
  busy: boolean;
}) {
  return (
    <>
      <h1 className="mt-4 text-h1 text-primary">Join the workspace.</h1>
      <p className="mt-6 text-body text-secondary">
        Accept to add this workspace to your account. You will land in the
        cases dashboard once you join.
      </p>
      <div className="mt-8 flex items-center gap-3">
        <button
          type="button"
          onClick={onAccept}
          disabled={busy}
          className="btn-lift rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:opacity-60"
        >
          {busy ? "Joining…" : "Accept invitation"}
        </button>
        <Link
          href="/cases"
          className="rounded-pill border border-border bg-surface px-4 py-2.5 text-body-sm text-primary transition-colors hover:bg-surface-muted"
        >
          Not now
        </Link>
      </div>
    </>
  );
}

function SuccessBlock({ invite }: { invite: WorkspaceInvitation }) {
  return (
    <>
      <h1 className="mt-4 text-h1 text-primary">You are in.</h1>
      <p className="mt-6 text-body text-secondary">
        You joined the workspace as a{" "}
        <span
          className={`inline-flex rounded-pill px-2.5 py-0.5 text-label-caps ${ROLE_TONE[invite.role]}`}
        >
          {invite.role}
        </span>
        . Redirecting to your cases dashboard…
      </p>
      <div className="mt-8">
        <Link
          href="/cases"
          className="rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
        >
          Go to cases now
        </Link>
      </div>
    </>
  );
}

function ErrorBlock({ message }: { message: string }) {
  return (
    <>
      <h1 className="mt-4 text-h1 text-primary">Invitation unavailable.</h1>
      <p className="mt-6 text-body text-secondary">{message}</p>
      <div className="mt-8 flex items-center gap-3">
        <Link
          href="/cases"
          className="rounded-pill border border-border bg-surface px-4 py-2.5 text-body-sm text-primary transition-colors hover:bg-surface-muted"
        >
          Back to cases
        </Link>
      </div>
    </>
  );
}

function invitationErrorMessage(err: WorkspaceError): string {
  if (err.status === 410) {
    return "This invitation has been used, revoked, or has expired. Ask the workspace admin to mint a fresh one.";
  }
  if (err.status === 401) {
    return "Sign in to accept this invitation.";
  }
  if (err.status === 404) {
    return "This invitation link is not recognised. Double-check the link you were sent.";
  }
  return err.message || "Could not accept invitation.";
}
