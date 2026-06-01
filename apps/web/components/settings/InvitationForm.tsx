"use client";

// Workspace invitation form (W9). A compact single row: a fixed-width email
// field, a small role select, and the Mint button, with the selected role's
// description as a quiet hint beneath. Once a mint succeeds the share link
// appears inline with a Copy button (SES delivery is a separate path; the
// admin can always paste the link in the meantime).

import { useEffect, useMemo, useState } from "react";

import type {
  WorkspaceError,
  WorkspaceInvitation,
  WorkspaceRole,
} from "@/lib/types";
import { createWorkspaceInvitation } from "@/lib/api";

const TOAST_TTL_MS = 5000;

// Invitations are minted as Member or Admin. Owner is reached by promotion on
// the members page, never by invite, so a workspace can't accidentally hand
// out billing control through a pasted link.
const ROLE_OPTIONS: { value: WorkspaceRole; label: string; hint: string }[] = [
  {
    value: "member",
    label: "Member",
    hint: "Day-to-day use: create and manage voyages.",
  },
  {
    value: "admin",
    label: "Admin",
    hint: "Manage members, invitations, and settings.",
  },
];

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function InvitationForm({
  workspaceId,
  onMinted,
}: {
  workspaceId: string;
  onMinted: (invite: WorkspaceInvitation) => void;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<WorkspaceRole>("member");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMinted, setLastMinted] = useState<WorkspaceInvitation | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  const roleHint = useMemo(
    () => ROLE_OPTIONS.find((o) => o.value === role)?.hint ?? "",
    [role],
  );

  useEffect(() => {
    if (copyState === "idle") return;
    const t = setTimeout(() => setCopyState("idle"), TOAST_TTL_MS);
    return () => clearTimeout(t);
  }, [copyState]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError(null);
    const trimmed = email.trim();
    if (!EMAIL_RE.test(trimmed)) {
      setError("Enter a valid email address.");
      return;
    }
    setBusy(true);
    try {
      const invite = await createWorkspaceInvitation(workspaceId, {
        email: trimmed,
        role,
      });
      setLastMinted(invite);
      onMinted(invite);
      setEmail("");
    } catch (e) {
      const err = e as WorkspaceError;
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleCopyLink() {
    if (!lastMinted) return;
    try {
      await navigator.clipboard.writeText(buildAcceptLink(lastMinted.token));
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  const invalid = Boolean(error);

  return (
    <section
      aria-label="Invite a teammate"
      className="rounded-card border border-border bg-surface p-6"
    >
      <p className="text-eyebrow text-secondary">Invite a teammate</p>
      <p className="mt-2 text-body-sm text-secondary">
        Send an invite link. They create an account and join this workspace.
      </p>

      {/* Tight, grouped row capped at a sensible width so the controls sit
          together instead of stretching across the whole settings column. */}
      <form onSubmit={handleSubmit} className="mt-5 max-w-xl">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1">
            <label
              htmlFor="invite-email"
              className="text-label-caps text-secondary"
            >
              Email
            </label>
            <input
              id="invite-email"
              type="email"
              inputMode="email"
              autoComplete="off"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (error) setError(null);
              }}
              required
              placeholder="teammate@example.com"
              aria-invalid={invalid || undefined}
              className={`mt-1.5 w-full rounded-md border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary ${
                invalid ? "border-danger" : "border-border"
              }`}
            />
          </div>

          <div className="sm:w-40">
            <label
              htmlFor="invite-role"
              className="text-label-caps text-secondary"
            >
              Role
            </label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value as WorkspaceRole)}
              className="mt-1.5 w-full rounded-md border border-border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary"
            >
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={busy}
            className="btn-lift shrink-0 whitespace-nowrap rounded-pill bg-cta px-5 py-2 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:opacity-60"
          >
            {busy ? "Inviting…" : "Send invite"}
          </button>
        </div>

        <p className="mt-2.5 text-body-sm text-secondary">{roleHint}</p>

        {error ? (
          <p role="alert" className="mt-2 text-body-sm text-danger">
            {error}
          </p>
        ) : null}

        <p className="mt-4 text-body-sm text-secondary">
          Invites are valid for 14 days. We do not send them by email yet, copy
          the link below to share.
        </p>
      </form>

      {lastMinted ? (
        <div className="mt-5 rounded-md border border-border bg-surface-muted p-4">
          <p className="text-eyebrow text-secondary">Share this link</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <code className="select-all break-all rounded-md bg-surface px-3 py-2 font-mono text-body-sm text-primary">
              {buildAcceptLink(lastMinted.token)}
            </code>
            <button
              type="button"
              onClick={handleCopyLink}
              className="rounded-pill border border-border bg-surface px-3 py-1.5 text-body-sm text-primary transition-colors hover:bg-surface-muted"
            >
              {copyState === "copied"
                ? "Copied"
                : copyState === "failed"
                  ? "Copy failed"
                  : "Copy link"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function buildAcceptLink(token: string): string {
  if (typeof window === "undefined") return `/invite/${token}`;
  return `${window.location.origin}/invite/${token}`;
}
