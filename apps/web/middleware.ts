// Edge middleware: enforce auth on every protected route.
//
// Rules:
//   - Unauthed request to a protected route -> 302 /login?next=<original-path>
//   - Authed request to /login              -> 302 /cases (no point re-signing in)
//   - /api/auth/* and static assets         -> passthrough (handled by `matcher`)
//
// The middleware runs in the Edge runtime, so it uses Web Crypto via the
// shared `verifySession()` helper.

import { NextResponse, type NextRequest } from "next/server";
import {
  LOGIN_PATH,
  NEXT_PARAM,
  POST_LOGIN_PATH,
  SESSION_COOKIE,
} from "@/lib/auth/constants";
import { verifySession } from "@/lib/auth/session";

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const session = await verifySession(token);

  const isLoginRoute = pathname === LOGIN_PATH;

  if (isLoginRoute) {
    if (session) {
      const url = request.nextUrl.clone();
      url.pathname = POST_LOGIN_PATH;
      url.search = "";
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  if (!session) {
    const url = request.nextUrl.clone();
    url.pathname = LOGIN_PATH;
    // Preserve the original destination so post-login lands the user back
    // where they were trying to go. Only forward same-origin paths.
    const dest = pathname + (search || "");
    url.search = `?${NEXT_PARAM}=${encodeURIComponent(dest)}`;
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Run on every route except: Next internals, static files, the favicon, and
// the auth API itself (it must be reachable for unauthed users to sign in).
export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico|logo.png|.*\\..*).*)"],
};
