"use client";

// SCREEN: /settings/inbox. Surfaces the workspace's forward-to inbox address
// + Gmail / Outlook tutorials (W7, notes/architecture_weeks_5_to_8.md §2.3).
//
// Workspace id: today every authed user gets a personal workspace whose id
// is the deterministic ``personal:<sub>`` slug (the backend mints it during
// ensure_personal_workspace). We compute it from /api/auth/me and avoid
// shipping a /me/workspaces endpoint just for this page. When the workspaces
// switcher lands (W8 + WORKSPACES_UI flag), this page reads the active
// workspace id from the global selector instead.

import { useEffect, useState } from "react";

import TopNav from "@/components/TopNav";
import InboxSetupCard from "@/components/settings/InboxSetupCard";
import { fetchInboxAddress } from "@/lib/api";
import type { InboxAddress } from "@/lib/types";

interface CurrentUser {
  sub: string;
  name: string;
}

export default function InboxSettingsPage() {
  const [address, setAddress] = useState<InboxAddress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const meRes = await fetch("/api/auth/me", { signal: controller.signal });
        if (!meRes.ok) throw new Error("Not signed in");
        const { user } = (await meRes.json()) as { user?: CurrentUser | null };
        if (!user) throw new Error("Not signed in");
        const workspaceId = `personal:${user.sub}`;
        const next = await fetchInboxAddress(workspaceId, controller.signal);
        setAddress(next);
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!controller.signal.aborted) setBusy(false);
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        <section className="flex flex-col gap-10 pb-12 pt-8 md:flex-row md:items-end md:justify-between md:gap-16 md:pt-12">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Settings</p>
            <h1 className="text-hero mt-4 text-primary">Email-in.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Forward voyage emails (brokers, agents, charterers) into
              Laytimely. We never read your mailbox. We only see what you
              forward.
            </p>
          </div>
        </section>

        {error && (
          <p
            role="alert"
            className="mb-8 rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger"
          >
            {error}
          </p>
        )}

        <InboxSetupCard address={address?.address ?? null} loading={busy} />
      </main>
    </div>
  );
}
