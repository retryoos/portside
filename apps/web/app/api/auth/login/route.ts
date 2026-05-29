// POST /api/auth/login. Verify credentials, mint a signed session cookie.
//
// On bad credentials we return a generic 401 with a stable shape so the client
// renders the same message regardless of which field was wrong (don't leak
// whether the username exists). On success we set the cookie via the response,
// not via cookies().set(), so it ships on this exact response.

import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
} from "@/lib/auth/constants";
import { verifyCredentials } from "@/lib/auth/credentials";
import { signSession } from "@/lib/auth/session";

interface LoginBody {
  username?: unknown;
  password?: unknown;
}

export async function POST(request: Request): Promise<Response> {
  let body: LoginBody;
  try {
    body = (await request.json()) as LoginBody;
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const username = typeof body.username === "string" ? body.username : "";
  const password = typeof body.password === "string" ? body.password : "";

  if (!username || !password) {
    return NextResponse.json(
      { error: "Username and password are required." },
      { status: 400 },
    );
  }

  const user = verifyCredentials(username, password);
  if (!user) {
    return NextResponse.json(
      { error: "Invalid username or password." },
      { status: 401 },
    );
  }

  const token = await signSession({ sub: user.sub, name: user.name });
  const response = NextResponse.json({
    user: { sub: user.sub, name: user.name },
  });
  response.cookies.set({
    name: SESSION_COOKIE,
    value: token,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
  return response;
}
