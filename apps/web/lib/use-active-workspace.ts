// Active workspace hook (W8). Single source of truth for which workspace
// settings pages and the TopNav switcher render. Source of truth is
// localStorage; first-load default is the personal workspace returned by
// /me/workspaces.
//
// Why a hook + localStorage instead of a context provider: the settings pages
// are independent routes and a provider higher up the tree would require
// wrapping every layout. The hook is small, dependency-free, and works in any
// "use client" component.

"use client";

import { useCallback, useEffect, useState } from "react";

import { listMyWorkspaces } from "@/lib/api";
import type { MyWorkspaceEntry } from "@/lib/types";

const STORAGE_KEY = "laytimely.activeWorkspaceId";

export interface ActiveWorkspaceState {
  workspaces: MyWorkspaceEntry[] | null;
  active: MyWorkspaceEntry | null;
  error: string | null;
  loading: boolean;
  setActive: (workspaceId: string) => void;
  refresh: () => void;
}

export function useActiveWorkspace(): ActiveWorkspaceState {
  const [workspaces, setWorkspaces] = useState<MyWorkspaceEntry[] | null>(null);
  const [activeId, setActiveId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(STORAGE_KEY);
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    listMyWorkspaces(controller.signal)
      .then((rows) => {
        if (controller.signal.aborted) return;
        setWorkspaces(rows);
        // Reconcile the stored active id against the live list. If the
        // stored id is no longer a workspace the caller is a member of,
        // fall back to the first row (typically the personal workspace).
        const stored = activeId;
        const reconciled =
          stored && rows.some((r) => r.workspace.id === stored)
            ? stored
            : (rows[0]?.workspace.id ?? null);
        setActiveId(reconciled);
        if (reconciled && typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, reconciled);
        }
      })
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
    // We intentionally ignore the activeId dependency on refresh: the
    // localStorage value is read inside the effect to avoid a refetch loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  const setActive = useCallback((workspaceId: string) => {
    setActiveId(workspaceId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, workspaceId);
    }
  }, []);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  const active =
    workspaces?.find((r) => r.workspace.id === activeId) ?? workspaces?.[0] ?? null;

  return { workspaces, active, error, loading, setActive, refresh };
}
