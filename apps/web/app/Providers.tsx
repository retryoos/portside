"use client";

// Root-level client provider tree. Currently mounts:
//   - ActiveWorkspaceProvider: shared /me/workspaces fetch across every
//     authed page (TopNav + /settings/*).
//
// Sits below the server-rendered <html><body> so any "use client" hooks
// in the rest of the tree can resolve to the same cached state.

import { ActiveWorkspaceProvider } from "@/lib/use-active-workspace";
import type { ReactNode } from "react";

export default function Providers({ children }: { children: ReactNode }) {
  return <ActiveWorkspaceProvider>{children}</ActiveWorkspaceProvider>;
}
