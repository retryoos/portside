"use client";

// Pending invitations table (W9). Lists rows from
// GET /workspaces/{id}/invitations: email, role chip, invited-at date,
// expiry, and a Copy-link button so the admin can re-share. Empty state
// renders an editorial "no pending invites" panel.

import { useEffect, useState } from "react";

import type { WorkspaceInvitation, WorkspaceRole } from "@/lib/types";

const TOAST_TTL_MS = 4000;

const ROLE_TONE: Record<WorkspaceRole, string> = {
  owner: "bg-primary text-on-primary",
  admin: "bg-success-container text-success",
  member: "bg-surface-muted text-primary",
  viewer: "bg-surface-muted text-secondary",
};

export default function InvitationsTable({
  invitations,
}: {
  invitations: WorkspaceInvitation[];
}) {
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  useEffect(() => {
    if (!copiedToken) return;
    const t = setTimeout(() => setCopiedToken(null), TOAST_TTL_MS);
    return () => clearTimeout(t);
  }, [copiedToken]);

  if (invitations.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface px-8 py-16 text-center">
        <p className="text-eyebrow text-secondary">No pending invites</p>
        <h2 className="text-h2 mt-4 text-primary">Nobody waiting.</h2>
        <p className="mx-auto mt-4 max-w-md text-body text-secondary">
          Mint an invitation above to add a teammate. Existing pending invites
          will appear here.
        </p>
      </div>
    );
  }

  async function copyLink(token: string) {
    const link = buildAcceptLink(token);
    try {
      await navigator.clipboard.writeText(link);
      setCopiedToken(token);
    } catch {
      setCopiedToken(null);
    }
  }

  return (
    <div className="overflow-hidden rounded-card border border-border bg-surface">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border bg-surface-muted text-label-caps text-secondary">
            <th className="px-4 py-3 text-left">Email</th>
            <th className="px-4 py-3 text-left">Role</th>
            <th className="px-4 py-3 text-left">Invited</th>
            <th className="px-4 py-3 text-left">Expires</th>
            <th className="px-4 py-3 text-right">Link</th>
          </tr>
        </thead>
        <tbody>
          {invitations.map((inv) => (
            <tr key={inv.id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 align-middle text-body-sm text-primary">
                {inv.email}
              </td>
              <td className="px-4 py-3 align-middle">
                <span
                  className={`inline-flex rounded-pill px-2.5 py-0.5 text-label-caps ${ROLE_TONE[inv.role]}`}
                >
                  {inv.role}
                </span>
              </td>
              <td className="px-4 py-3 align-middle text-body-sm tabular-nums text-secondary">
                {formatDate(inv.invited_at)}
              </td>
              <td className="px-4 py-3 align-middle text-body-sm tabular-nums text-secondary">
                {formatDate(inv.expires_at)}
              </td>
              <td className="px-4 py-3 align-middle text-right">
                <button
                  type="button"
                  onClick={() => copyLink(inv.token)}
                  className="rounded-pill border border-border bg-surface px-3 py-1.5 text-body-sm text-primary transition-colors hover:bg-surface-muted"
                >
                  {copiedToken === inv.token ? "Copied" : "Copy link"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function buildAcceptLink(token: string): string {
  if (typeof window === "undefined") return `/invite/${token}`;
  return `${window.location.origin}/invite/${token}`;
}
