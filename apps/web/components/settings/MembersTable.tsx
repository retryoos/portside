"use client";

// Workspace members table (W8, notes/architecture_weeks_5_to_8.md §2.1).
// Plain list, role chip, Remove button. The Remove button surfaces the
// backend's stable "last_owner" code as a friendly toast: an admin who
// tries to remove the last owner is told to promote another member first
// rather than being shown a raw 409. The caller's own row is highlighted
// (no Remove button if removing self would leave the workspace ownerless;
// the backend enforces this and the UI mirrors it client-side for clarity).

import { useEffect, useState } from "react";

import type {
  WorkspaceError,
  WorkspaceMember,
  WorkspaceRole,
} from "@/lib/types";
import { removeWorkspaceMember } from "@/lib/api";

const TOAST_TTL_MS = 5000;

const ROLE_TONE: Record<WorkspaceRole, string> = {
  owner: "bg-primary text-on-primary",
  admin: "bg-success-container text-success",
  member: "bg-surface-muted text-primary",
  viewer: "bg-surface-muted text-secondary",
};

export default function MembersTable({
  workspaceId,
  members,
  callerSub,
  onChanged,
}: {
  workspaceId: string;
  members: WorkspaceMember[];
  callerSub: string | null;
  onChanged: () => void;
}) {
  const [busySub, setBusySub] = useState<string | null>(null);
  const [toast, setToast] = useState<{
    kind: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), TOAST_TTL_MS);
    return () => clearTimeout(t);
  }, [toast]);

  const ownerCount = members.filter((m) => m.role === "owner").length;

  async function handleRemove(member: WorkspaceMember) {
    if (busySub) return;
    setBusySub(member.user_sub);
    try {
      await removeWorkspaceMember(workspaceId, member.user_sub);
      setToast({ kind: "success", message: `Removed ${shortSub(member.user_sub)}` });
      onChanged();
    } catch (e) {
      const err = e as WorkspaceError;
      const message =
        err.code === "last_owner"
          ? "Promote another member to owner before removing the last owner."
          : err.message;
      setToast({ kind: "error", message });
    } finally {
      setBusySub(null);
    }
  }

  if (members.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface px-8 py-16 text-center">
        <p className="text-eyebrow text-secondary">No members</p>
        <h2 className="text-h2 mt-4 text-primary">This workspace is empty.</h2>
        <p className="mx-auto mt-4 max-w-md text-body text-secondary">
          Mint an invitation to add a teammate.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-card border border-border bg-surface">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-label-caps text-secondary">
              <th className="px-4 py-3 text-left">Member</th>
              <th className="px-4 py-3 text-left">Role</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => {
              const isSelf = callerSub !== null && m.user_sub === callerSub;
              const wouldStrandWorkspace =
                m.role === "owner" && ownerCount <= 1;
              const removeDisabled = wouldStrandWorkspace || busySub === m.user_sub;
              return (
                <tr key={m.user_sub} className="border-b border-border last:border-b-0">
                  <td className="px-4 py-3 align-middle text-body-sm text-primary">
                    <span className="font-medium">{shortSub(m.user_sub)}</span>
                    {isSelf ? (
                      <span className="ml-2 text-label-caps text-secondary">
                        You
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 align-middle">
                    <span
                      className={`inline-flex rounded-pill px-2.5 py-0.5 text-label-caps ${ROLE_TONE[m.role]}`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-middle text-right">
                    <button
                      type="button"
                      onClick={() => handleRemove(m)}
                      disabled={removeDisabled}
                      title={
                        wouldStrandWorkspace
                          ? "Cannot remove the only owner"
                          : isSelf
                            ? "Leave workspace"
                            : "Remove member"
                      }
                      className="rounded-pill border border-border bg-surface px-3 py-1.5 text-body-sm text-primary transition-colors hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {busySub === m.user_sub
                        ? "Removing…"
                        : isSelf
                          ? "Leave"
                          : "Remove"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {toast ? <MembersToast kind={toast.kind} message={toast.message} /> : null}
    </>
  );
}

function MembersToast({
  kind,
  message,
}: {
  kind: "success" | "error";
  message: string;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-6 right-6 z-50 max-w-sm rounded-card border border-border bg-surface px-4 py-3 shadow-lg"
    >
      <div className="flex items-start gap-2">
        <span
          aria-hidden
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
            kind === "success"
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
            {kind === "success" ? (
              <path d="m5 12 4 4 10-10" />
            ) : (
              <path d="M12 8v5M12 17h.01" />
            )}
          </svg>
        </span>
        <p className="text-body-sm text-primary">{message}</p>
      </div>
    </div>
  );
}

function shortSub(sub: string): string {
  if (sub.length <= 28) return sub;
  return sub.slice(0, 8) + "…" + sub.slice(-12);
}
