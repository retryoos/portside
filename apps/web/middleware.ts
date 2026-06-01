// Edge middleware: the line of defence between the public marketing site and
// the authenticated product. Rules:
//
//   - Public marketing routes (allowlisted below) -> passthrough.
//   - Auth API + Next.js internals (handled by `matcher`) -> passthrough.
//   - /login: passthrough when unauthed; redirected to /cases when authed.
//   - Everything else: requires a valid session cookie. Missing or invalid
//     session -> 302 /login?next=<original-path>.
//
// The default is DENY so a new protected route is gated until the matcher is
// updated. New public routes must be added to PUBLIC_EXACT.
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

// Marketing surfaces. Visitors reach these without a session.
const PUBLIC_EXACT = new Set<string>([
  "/",
  "/about",
  "/security",
  "/privacy",
  "/terms",
  "/contact",
]);

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Public marketing routes: passthrough.
  if (PUBLIC_EXACT.has(pathname)) {
    return NextResponse.next();
  }

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const session = await verifySession(token);

  const isLoginRoute = pathname === LOGIN_PATH;
  // /invite/<token> (W9) is technically open to any authed user (even one
  // who is not yet a member of any workspace), but the existing default
  // flow already handles that: unauthed -> redirected to /login with the
  // invite path preserved as `next`, signed-in -> page renders + the
  // accept POST mints the workspace membership. No allowlist change
  // needed; this comment documents the intent for the next reviewer.

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

// Run on every route except: Next internals, static files, the favicon, the
// photography and showcase asset directories, and the auth API.
export const config = {
  matcher: [
    "/((?!api/auth|_next/static|_next/image|favicon.ico|logo.png|photography|showcase|.*\\..*).*)",
  ],
};
