"use client";

// Workspace invitation form (W9). Email + role select + Mint button. The
// "share link" output sits inline beneath the form once the mint succeeds,
// with a Copy button: SES delivery is a separate path tracked in the
// production checklist, but the admin can always paste the link manually
// in the meantime.

import { useEffect, useState } from "react";

import type {
  WorkspaceError,
  WorkspaceInvitation,
  WorkspaceRole,
} from "@/lib/types";
import { createWorkspaceInvitation } from "@/lib/api";

const TOAST_TTL_MS = 5000;

const ROLE_OPTIONS: { value: WorkspaceRole; label: string }[] = [
  { value: "viewer", label: "Viewer — read-only" },
  { value: "member", label: "Member — day-to-day use" },
  { value: "admin", label: "Admin — manage members + settings" },
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
    const link = buildAcceptLink(lastMinted.token);
    try {
      await navigator.clipboard.writeText(link);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <section
      aria-label="Mint invitation"
      className="rounded-card border border-border bg-surface p-6"
    >
      <p className="text-eyebrow text-secondary">Mint invitation</p>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div className="grid gap-4 md:grid-cols-[1fr_auto]">
          <div>
            <label htmlFor="invite-email" className="text-label-caps text-secondary">
              Email
            </label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="teammate@example.com"
              className="mt-2 w-full rounded-card border border-border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary"
            />
          </div>
          <div>
            <label htmlFor="invite-role" className="text-label-caps text-secondary">
              Role
            </label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value as WorkspaceRole)}
              className="mt-2 rounded-card border border-border bg-surface px-3 py-2 text-body text-primary outline-none transition-colors focus:border-primary"
            >
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        {error ? (
          <p role="alert" className="text-body-sm text-danger">
            {error}
          </p>
        ) : null}
        <div className="flex items-center justify-between gap-4">
          <p className="text-body-sm text-secondary">
            Invitations expire in 14 days. We do not email yet — copy the
            link from the row below to share it.
          </p>
          <button
            type="submit"
            disabled={busy}
            className="btn-lift rounded-pill bg-cta px-5 py-2 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:opacity-60"
          >
            {busy ? "Minting…" : "Mint invitation"}
          </button>
        </div>
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
