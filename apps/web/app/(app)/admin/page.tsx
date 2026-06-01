"use client";

// SCREEN: /admin (founders-only usage + activity dashboard). The real gate is
// server-side: /admin/overview returns 403 unless the caller's email is on the
// API's ADMIN_EMAILS allowlist. This page renders a clean "not authorized"
// state on 403, so it is safe even though the route itself only requires login.

import { useEffect, useState } from "react";

import TopNav from "@/components/TopNav";
import { getAdminEvents, getAdminOverview } from "@/lib/api";
import type { AdminAuthEvent, AdminOverview, UsageBucket } from "@/lib/types";

const WINDOWS = [7, 30, 90];

const ACTION_LABEL: Record<string, string> = {
  "auth.signup": "Sign up",
  "auth.login": "Sign in",
  "auth.login_failed": "Failed login",
  "auth.demo": "Demo start",
};

function usd(n: number): string {
  return `$${n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function num(n: number): string {
  return n.toLocaleString();
}

export default function AdminPage() {
  const [days, setDays] = useState(30);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [events, setEvents] = useState<AdminAuthEvent[] | null>(null);
  const [denied, setDenied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    setDenied(false);
    setOverview(null);
    Promise.all([
      getAdminOverview(days, controller.signal),
      getAdminEvents(50, controller.signal),
    ])
      .then(([ov, ev]) => {
        setOverview(ov);
        setEvents(ev);
      })
      .catch((e: unknown) => {
        if (controller.signal.aborted) return;
        const status = (e as { status?: number }).status;
        if (status === 403) setDenied(true);
        else setError(e instanceof Error ? e.message : String(e));
      });
    return () => controller.abort();
  }, [days]);

  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[1100px] px-6 pb-24 md:px-8">
        <section className="flex flex-col gap-6 pb-10 pt-8 md:flex-row md:items-end md:justify-between md:pt-12">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-secondary">Admin</p>
            <h1 className="text-hero mt-4 text-primary">Usage and activity.</h1>
            <p className="mt-6 max-w-xl text-body-lg text-secondary">
              Token spend, sign-ups, and sign-ins across all accounts.
              Estimated cost is indicative; the Anthropic Console is the billing
              source of truth.
            </p>
          </div>
          {!denied && (
            <div className="flex gap-2" role="group" aria-label="Time window">
              {WINDOWS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setDays(w)}
                  className={`rounded-pill border px-3.5 py-1.5 text-body-sm transition-colors ${
                    days === w
                      ? "border-primary bg-primary text-on-primary"
                      : "border-border bg-surface text-primary hover:bg-surface-muted"
                  }`}
                >
                  {w}d
                </button>
              ))}
            </div>
          )}
        </section>

        {denied ? (
          <Denied />
        ) : error ? (
          <p
            role="alert"
            className="rounded-card border border-danger/20 bg-danger-container px-5 py-4 text-body-sm text-danger"
          >
            {error}
          </p>
        ) : !overview ? (
          <p className="text-body text-secondary">Loading…</p>
        ) : (
          <div className="space-y-10">
            <StatGrid o={overview} />
            <BucketTable
              title="By API key"
              hint="Which rotating key is spending. Grouped by key label or fingerprint."
              rows={overview.by_key}
              keyHead="Key"
            />
            <div className="grid gap-10 lg:grid-cols-2">
              <BucketTable title="By model" rows={overview.by_model} keyHead="Model" />
              <BucketTable
                title="By feature"
                rows={overview.by_feature}
                keyHead="Feature"
              />
            </div>
            <BucketTable
              title="Top users"
              hint="Highest token spend. Label is the account email."
              rows={overview.top_users}
              keyHead="User"
            />
            <RecentEvents events={events ?? []} />
          </div>
        )}
      </main>
    </div>
  );
}

function StatGrid({ o }: { o: AdminOverview }) {
  const stats: { label: string; value: string }[] = [
    { label: "Est. cost (USD)", value: usd(o.est_cost_usd) },
    { label: "Model calls", value: num(o.total_calls) },
    { label: "Input tokens", value: num(o.total_input_tokens) },
    { label: "Output tokens", value: num(o.total_output_tokens) },
    { label: "Sign-ups", value: num(o.signups) },
    { label: "Sign-ins", value: num(o.logins) },
    { label: "Failed logins", value: num(o.login_failures) },
    { label: "Demo starts", value: num(o.demo_starts) },
  ];
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-card border border-border bg-surface p-5"
        >
          <p className="text-label-caps text-secondary">{s.label}</p>
          <p className="text-h2 mt-2 text-primary">{s.value}</p>
        </div>
      ))}
    </div>
  );
}

function BucketTable({
  title,
  hint,
  rows,
  keyHead,
}: {
  title: string;
  hint?: string;
  rows: UsageBucket[];
  keyHead: string;
}) {
  return (
    <section>
      <h2 className="text-h3 text-primary">{title}</h2>
      {hint ? <p className="mt-1 text-body-sm text-secondary">{hint}</p> : null}
      <div className="mt-4 overflow-hidden rounded-card border border-border bg-surface">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-label-caps text-secondary">
              <th className="px-4 py-3 text-left">{keyHead}</th>
              <th className="px-4 py-3 text-right">Calls</th>
              <th className="px-4 py-3 text-right">Input</th>
              <th className="px-4 py-3 text-right">Output</th>
              <th className="px-4 py-3 text-right">Est. cost</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-6 text-center text-body-sm text-secondary"
                >
                  No usage in this window yet.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr
                  key={r.key}
                  className="border-b border-border text-body-sm last:border-b-0"
                >
                  <td className="px-4 py-3 text-primary">
                    <span className="font-medium">{r.label || r.key}</span>
                    {r.label && r.label !== r.key ? (
                      <span className="ml-2 font-mono text-secondary">
                        {r.key}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-secondary">
                    {num(r.calls)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-secondary">
                    {num(r.input_tokens)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-secondary">
                    {num(r.output_tokens)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-medium text-primary">
                    {usd(r.est_cost_usd)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function RecentEvents({ events }: { events: AdminAuthEvent[] }) {
  return (
    <section>
      <h2 className="text-h3 text-primary">Recent activity</h2>
      <div className="mt-4 overflow-hidden rounded-card border border-border bg-surface">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-label-caps text-secondary">
              <th className="px-4 py-3 text-left">When</th>
              <th className="px-4 py-3 text-left">Event</th>
              <th className="px-4 py-3 text-left">Account</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td
                  colSpan={3}
                  className="px-4 py-6 text-center text-body-sm text-secondary"
                >
                  No activity yet.
                </td>
              </tr>
            ) : (
              events.map((e, i) => (
                <tr
                  key={`${e.at}-${i}`}
                  className="border-b border-border text-body-sm last:border-b-0"
                >
                  <td className="px-4 py-3 text-secondary">
                    {new Date(e.at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-primary">
                    {ACTION_LABEL[e.action] ?? e.action}
                  </td>
                  <td className="px-4 py-3 text-secondary">
                    {e.email || e.target_id || e.actor_sub || "unknown"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Denied() {
  return (
    <div className="rounded-card border border-border bg-surface px-8 py-16 text-center">
      <p className="text-eyebrow text-secondary">Restricted</p>
      <h2 className="text-h2 mt-4 text-primary">Admins only.</h2>
      <p className="mx-auto mt-4 max-w-md text-body text-secondary">
        This dashboard is limited to the Laytimely admin accounts. If you should
        have access, ask to be added to the admin allowlist.
      </p>
    </div>
  );
}
