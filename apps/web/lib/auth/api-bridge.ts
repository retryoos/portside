// Server-only helpers shared by the /api/auth/{login,signup} route handlers.
//
// These routes proxy credentials to the backend and store the JWT it returns
// in the httpOnly session cookie. Keeping the API base URL resolution and the
// cookie-setting in one place stops the two routes from drifting.

import type { NextResponse } from "next/server";

// Same default the browser client uses (lib/api.ts). A server-only override
// (API_INTERNAL_URL) lets a deploy point route handlers at an internal address
// while the browser uses the public one.
export function apiBaseUrl(): string {
  const raw =
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

export function setSessionCookie(
  response: NextResponse,
  name: string,
  value: string,
  maxAge: number,
): void {
  response.cookies.set({
    name,
    value,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  });
}
