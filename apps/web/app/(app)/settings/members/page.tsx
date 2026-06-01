"use client";

// SCREEN: /settings/members (W8, notes/architecture_weeks_5_to_8.md §2.1).
// Renders the membership list for the active workspace, sourced from
// /workspaces/{id}/members. The active workspace comes from the shared
// useActiveWorkspace hook; the switcher in TopNav writes it.

import { useEffect, useState } from "react";

import TopNav from "@/components/TopNav";
import MembersTable from "@/components/settings/MembersTable";
import { listWorkspaceMembers } from "@/lib/api";
import { useActiveWorkspace } from "@/lib/use-active-workspace";
import type { WorkspaceMember } from "@/lib/types";

interface CurrentUser {
  sub: string;
  name: string;
}

export default function MembersPage() {
  const { active, loading: wsLoading, error: wsError } = useActiveWorkspace();
  const [callerSub, setCallerSub] = useState<string | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[] | null>(null);
  const [tick, setTick] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Fetch /api/auth/me once for the "You" badge in the table.
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/auth/me", { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { user?: CurrentUser | null } | null) => {
        if (data?.user) setCallerSub(data.user.sub);
      })
      .catch(() => {
        /* the chip and the table both render fine without it */
      });
    return () => controller.abort();
  }, []);

  // Re-fetch members whenever the active workspace changes or the user
  // triggers a refresh after a remove.
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    setError(null);
    setMembers(null);
    listWorkspaceMembers(active.workspace.id, controller.signal)
      .then((rows) => setMembers(rows))
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
            <h1 className="text-hero mt-4 text-primary">Members.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Everyone with access to{" "}
              <span className="font-medium text-primary">
                {active?.workspace.name ?? "this workspace"}
              </span>
              . Change a person&apos;s role or remove them. Every workspace
              keeps at least one owner.
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
          <SkeletonRows />
        ) : !isAdmin ? (
          <div className="rounded-card border border-border bg-surface px-8 py-16 text-center">
            <p className="text-eyebrow text-secondary">Read-only</p>
            <h2 className="text-h2 mt-4 text-primary">Admins manage members.</h2>
            <p className="mx-auto mt-4 max-w-md text-body text-secondary">
              You are a {active.role} in this workspace. Ask an owner or admin
              to add or remove members.
            </p>
          </div>
        ) : members === null ? (
          <SkeletonRows />
        ) : (
          <MembersTable
            workspaceId={active.workspace.id}
            members={members}
            callerSub={callerSub}
            onChanged={() => setTick((t) => t + 1)}
          />
        )}
      </main>
    </div>
  );
}

function SkeletonRows() {
  return (
    <div
      aria-busy
      aria-label="Loading members"
      className="overflow-hidden rounded-card border border-border bg-surface"
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 border-b border-border px-6 py-5 last:border-b-0"
        >
          <div className="space-y-2">
            <div className="h-3 w-44 rounded animate-shimmer" />
            <div className="h-2.5 w-24 rounded animate-shimmer" />
          </div>
          <div className="h-5 w-20 rounded-pill animate-shimmer" />
          <div className="h-7 w-20 rounded-pill animate-shimmer" />
        </div>
      ))}
    </div>
  );
}
