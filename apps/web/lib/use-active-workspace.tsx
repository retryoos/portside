// Active workspace context (W8, hardened post-review #6 + post-launch fix).
// One fetch of /me/workspaces per mounted ActiveWorkspaceProvider; every
// consumer reads the same cached state via React Context.
//
// SSR safety: the source of truth for the active workspace id is
// localStorage, but ``useState`` initializers that read it would diverge
// between the server (null) and the first client render (whatever was
// stored). React 19 surfaces such mismatches as "Invalid hook call" /
// "Cannot read properties of null" further down the tree. We therefore
// initialize null on both server and client, then sync from localStorage
// inside a client-only useEffect — standard hydration-safe pattern.

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

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

const ActiveWorkspaceContext = createContext<ActiveWorkspaceState | null>(null);

const EMPTY_STATE: ActiveWorkspaceState = {
  workspaces: null,
  active: null,
  error: null,
  loading: false,
  setActive: () => undefined,
  refresh: () => undefined,
};

export function ActiveWorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaces, setWorkspaces] = useState<MyWorkspaceEntry[] | null>(null);
  // Always null on first render so the server's HTML matches the client's
  // first paint. Localstorage gets read in the useEffect below.
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    // Client-only: sync activeId from localStorage before the fetch
    // resolves so a known stored id is honoured immediately.
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) setActiveId(stored);
    }

    listMyWorkspaces(controller.signal)
      .then((rows) => {
        if (controller.signal.aborted) return;
        setWorkspaces(rows);
        if (typeof window !== "undefined") {
          const stored = window.localStorage.getItem(STORAGE_KEY);
          const reconciled =
            stored && rows.some((r) => r.workspace.id === stored)
              ? stored
              : (rows[0]?.workspace.id ?? null);
          setActiveId(reconciled);
          if (reconciled) {
            window.localStorage.setItem(STORAGE_KEY, reconciled);
          }
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
  }, [tick]);

  const setActive = useCallback((workspaceId: string) => {
    setActiveId(workspaceId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, workspaceId);
    }
  }, []);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  const value = useMemo<ActiveWorkspaceState>(
    () => ({
      workspaces,
      active:
        workspaces?.find((r) => r.workspace.id === activeId) ??
        workspaces?.[0] ??
        null,
      error,
      loading,
      setActive,
      refresh,
    }),
    [workspaces, activeId, error, loading, setActive, refresh],
  );

  return (
    <ActiveWorkspaceContext.Provider value={value}>
      {children}
    </ActiveWorkspaceContext.Provider>
  );
}

/**
 * Read the shared active workspace state.
 *
 * Returns a no-op ``EMPTY_STATE`` when no provider is mounted (the case
 * for SSR-only paths and isolated test mounts) so callers never have to
 * branch on a null context. The provider lives at the app root layout
 * (apps/web/app/Providers.tsx), so any authed page automatically gets
 * real state.
 */
export function useActiveWorkspace(): ActiveWorkspaceState {
  const ctx = useContext(ActiveWorkspaceContext);
  return ctx ?? EMPTY_STATE;
}
