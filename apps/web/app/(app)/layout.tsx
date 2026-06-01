// Layout for every authenticated product route. Mounting <Providers>
// here (rather than in the root layout) means marketing visits to ``/``,
// ``/contact``, ``/login``, etc. never instantiate ActiveWorkspaceProvider,
// which in turn never fires the ``/api/auth/token`` + ``/me/workspaces``
// probe. Cuts the wasted 401 invocations Vercel was logging on every
// landing-page hit.
//
// The route group ``(app)`` is URL-invisible: ``app/(app)/cases`` still
// serves at ``/cases``.

import type { ReactNode } from "react";
import Providers from "../Providers";

export default function AppLayout({ children }: { children: ReactNode }) {
  return <Providers>{children}</Providers>;
}
