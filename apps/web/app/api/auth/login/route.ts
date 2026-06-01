// POST /api/auth/login. Proxies email/password to the backend /auth/login,
// then stores the backend-issued JWT in the httpOnly session cookie so the
// middleware, /api/auth/me, and /api/auth/token all see the same real session.
//
// The backend token is never exposed to client JS: it is set HttpOnly here and
// only read back by same-origin server routes. Bad credentials return a
// generic 401 so we don't leak whether an email is registered.

import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/constants";
import { apiBaseUrl, setSessionCookie } from "@/lib/auth/api-bridge";

interface LoginBody {
  email?: unknown;
  password?: unknown;
}

export async function POST(request: Request): Promise<Response> {
  let body: LoginBody;
  try {
    body = (await request.json()) as LoginBody;
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const email = typeof body.email === "string" ? body.email.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  if (!email || !password) {
    return NextResponse.json(
      { error: "Email and password are required." },
      { status: 400 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return NextResponse.json(
      { error: "Could not reach the server. Try again." },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const status = upstream.status === 429 ? 429 : 401;
    const message =
      status === 429
        ? "Too many attempts. Please wait a moment and try again."
        : "Invalid email or password.";
    return NextResponse.json({ error: message }, { status });
  }

  const data = (await upstream.json()) as {
    token?: string;
    user?: { sub: string; email: string | null; name: string | null };
  };
  if (!data.token) {
    return NextResponse.json(
      { error: "Sign in failed. Please try again." },
      { status: 502 },
    );
  }

  const response = NextResponse.json({ user: data.user ?? null });
  setSessionCookie(response, SESSION_COOKIE, data.token, SESSION_MAX_AGE_SECONDS);
  return response;
}
