// Active workspace context (W8, hardened post-review #6). One fetch of
// /me/workspaces per mounted ActiveWorkspaceProvider; every consumer reads
// the same cached state via React Context. Source of truth for the active
// workspace is localStorage; first-load default is the personal workspace
// returned by /me/workspaces.
//
// Hook contract is unchanged — components that previously called
// useActiveWorkspace continue to work; what changes is that under an
// ActiveWorkspaceProvider all of them share one fetch and re-renders
// stay in sync (e.g. switching workspace in the TopNav chip immediately
// updates the /settings/members page).

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

export function ActiveWorkspaceProvider({ children }: { children: ReactNode }) {
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
 * When mounted under an ``ActiveWorkspaceProvider`` (the production path,
 * via the (app) layout) every consumer reads the same cached fetch. When
 * mounted outside one (e.g. an isolated component test) the hook falls
 * back to a one-off internal fetch so callers do not need to wrap test
 * mounts in a provider.
 */
export function useActiveWorkspace(): ActiveWorkspaceState {
  const ctx = useContext(ActiveWorkspaceContext);
  // Standalone fallback: replicate the original behaviour for any consumer
  // mounted outside a provider. This keeps tests + ad-hoc usage working
  // even though production wraps everything in the provider.
  const [fallbackWorkspaces, setFallbackWorkspaces] = useState<
    MyWorkspaceEntry[] | null
  >(null);
  const [fallbackActiveId, setFallbackActiveId] = useState<string | null>(
    () => {
      if (typeof window === "undefined") return null;
      return window.localStorage.getItem(STORAGE_KEY);
    },
  );
  const [fallbackError, setFallbackError] = useState<string | null>(null);
  const [fallbackLoading, setFallbackLoading] = useState(true);
  const [fallbackTick, setFallbackTick] = useState(0);

  useEffect(() => {
    if (ctx) return; // Provider is responsible; do nothing.
    const controller = new AbortController();
    setFallbackLoading(true);
    listMyWorkspaces(controller.signal)
      .then((rows) => {
        if (controller.signal.aborted) return;
        setFallbackWorkspaces(rows);
        if (typeof window !== "undefined") {
          const stored = window.localStorage.getItem(STORAGE_KEY);
          const reconciled =
            stored && rows.some((r) => r.workspace.id === stored)
              ? stored
              : (rows[0]?.workspace.id ?? null);
          setFallbackActiveId(reconciled);
          if (reconciled) {
            window.localStorage.setItem(STORAGE_KEY, reconciled);
          }
        }
      })
      .catch((e) => {
        if (controller.signal.aborted) return;
        setFallbackError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setFallbackLoading(false);
      });
    return () => controller.abort();
  }, [ctx, fallbackTick]);

  const setActiveFallback = useCallback((workspaceId: string) => {
    setFallbackActiveId(workspaceId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, workspaceId);
    }
  }, []);

  const refreshFallback = useCallback(() => setFallbackTick((t) => t + 1), []);

  if (ctx) return ctx;
  return {
    workspaces: fallbackWorkspaces,
    active:
      fallbackWorkspaces?.find((r) => r.workspace.id === fallbackActiveId) ??
      fallbackWorkspaces?.[0] ??
      null,
    error: fallbackError,
    loading: fallbackLoading,
    setActive: setActiveFallback,
    refresh: refreshFallback,
  };
}
