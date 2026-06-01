// POST /api/auth/signup. Proxies to the backend /auth/signup, then stores the
// backend-issued JWT in the httpOnly session cookie (same as login) so a fresh
// account is signed in immediately. 409 if the email is already registered.

import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/constants";
import { apiBaseUrl, setSessionCookie } from "@/lib/auth/api-bridge";

interface SignupBody {
  email?: unknown;
  password?: unknown;
  name?: unknown;
}

const MIN_PASSWORD = 8;

export async function POST(request: Request): Promise<Response> {
  let body: SignupBody;
  try {
    body = (await request.json()) as SignupBody;
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const email = typeof body.email === "string" ? body.email.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  const name =
    typeof body.name === "string" && body.name.trim() ? body.name.trim() : null;

  if (!email || !password) {
    return NextResponse.json(
      { error: "Email and password are required." },
      { status: 400 },
    );
  }
  if (password.length < MIN_PASSWORD) {
    return NextResponse.json(
      { error: `Password must be at least ${MIN_PASSWORD} characters.` },
      { status: 400 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/signup`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });
  } catch {
    return NextResponse.json(
      { error: "Could not reach the server. Try again." },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    if (upstream.status === 409) {
      return NextResponse.json(
        { error: "An account with this email already exists. Sign in instead." },
        { status: 409 },
      );
    }
    if (upstream.status === 429) {
      return NextResponse.json(
        { error: "Too many attempts. Please wait a moment and try again." },
        { status: 429 },
      );
    }
    return NextResponse.json(
      { error: "Could not create the account. Check your details and try again." },
      { status: 400 },
    );
  }

  const data = (await upstream.json()) as {
    token?: string;
    user?: { sub: string; email: string | null; name: string | null };
  };
  if (!data.token) {
    return NextResponse.json(
      { error: "Sign up failed. Please try again." },
      { status: 502 },
    );
  }

  const response = NextResponse.json({ user: data.user ?? null });
  setSessionCookie(response, SESSION_COOKIE, data.token, SESSION_MAX_AGE_SECONDS);
  return response;
}
