// POST /api/auth/demo. One-click demo sign-in: asks the backend for a session
// token bound to the shared demo identity (which owns the seeded case data),
// then stores it in the httpOnly cookie exactly like login. Lets a prospect
// land in a populated app from the marketing site without an account.

import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/constants";
import { apiBaseUrl, setSessionCookie } from "@/lib/auth/api-bridge";

export async function POST(): Promise<Response> {
  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/demo`, { method: "POST" });
  } catch {
    return NextResponse.json(
      { error: "Could not start the demo. Try again." },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const status = upstream.status === 429 ? 429 : 502;
    return NextResponse.json(
      {
        error:
          status === 429
            ? "Too many attempts. Please wait a moment and try again."
            : "Could not start the demo. Try again.",
      },
      { status },
    );
  }

  const data = (await upstream.json()) as {
    token?: string;
    user?: { sub: string; email: string | null; name: string | null };
  };
  if (!data.token) {
    return NextResponse.json(
      { error: "Could not start the demo. Try again." },
      { status: 502 },
    );
  }

  const response = NextResponse.json({ user: data.user ?? null });
  setSessionCookie(response, SESSION_COOKIE, data.token, SESSION_MAX_AGE_SECONDS);
  return response;
}
