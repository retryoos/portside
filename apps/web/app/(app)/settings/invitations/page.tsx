"use client";

// SCREEN: /settings/invitations (W9). Admin-only view to mint a new
// invitation and re-share existing pending ones. The active workspace
// comes from the shared useActiveWorkspace hook; the form posts to
// POST /workspaces/{id}/invitations and the table reads
// GET /workspaces/{id}/invitations.

import { useEffect, useState } from "react";

import TopNav from "@/components/TopNav";
import InvitationForm from "@/components/settings/InvitationForm";
import InvitationsTable from "@/components/settings/InvitationsTable";
import { listWorkspaceInvitations } from "@/lib/api";
import { useActiveWorkspace } from "@/lib/use-active-workspace";
import type { WorkspaceInvitation } from "@/lib/types";

export default function InvitationsPage() {
  const { active, loading: wsLoading, error: wsError } = useActiveWorkspace();
  const [invitations, setInvitations] = useState<WorkspaceInvitation[] | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    setError(null);
    setInvitations(null);
    listWorkspaceInvitations(active.workspace.id, controller.signal)
      .then((rows) => setInvitations(rows))
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      });
    return () => controller.abort();
  }, [active, tick]);

  const isAdmin = active?.role === "owner" || active?.role === "admin";
  const errMsg = wsError ?? error;

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        <section className="flex flex-col gap-10 pb-12 pt-8 md:flex-row md:items-end md:justify-between md:gap-16 md:pt-12">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Settings</p>
            <h1 className="text-hero mt-4 text-primary">Invitations.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Invite teammates to{" "}
              <span className="font-medium text-primary">
                {active?.workspace.name ?? "this workspace"}
              </span>
              , and re-share any pending invites. Each invite is valid for 14
              days.
            </p>
          </div>
        </section>

        {errMsg && (
          <p
            role="alert"
            className="mb-8 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger"
          >
            {errMsg}
          </p>
        )}

        {wsLoading || !active ? (
          <Skeleton />
        ) : !isAdmin ? (
          <div className="rounded-card border border-border bg-surface px-8 py-16 text-center">
            <p className="text-eyebrow text-secondary">Read-only</p>
            <h2 className="text-h2 mt-4 text-primary">Admins mint invites.</h2>
            <p className="mx-auto mt-4 max-w-md text-body text-secondary">
              You are a {active.role} in this workspace. Ask an owner or admin
              to invite a teammate.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            <InvitationForm
              workspaceId={active.workspace.id}
              onMinted={() => setTick((t) => t + 1)}
            />
            <section>
              <p className="text-eyebrow text-secondary">Pending invitations</p>
              <div className="mt-4">
                {invitations === null ? (
                  <Skeleton />
                ) : (
                  <InvitationsTable
                    invitations={invitations}
                    workspaceId={active.workspace.id}
                    onChanged={() => setTick((t) => t + 1)}
                  />
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

function Skeleton() {
  return (
    <div
      aria-busy
      className="overflow-hidden rounded-card border border-border bg-surface"
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 border-b border-border px-6 py-5 last:border-b-0"
        >
          <div className="h-3 w-56 rounded animate-shimmer" />
          <div className="h-5 w-20 rounded-pill animate-shimmer" />
          <div className="h-3 w-24 rounded animate-shimmer" />
        </div>
      ))}
    </div>
  );
}
