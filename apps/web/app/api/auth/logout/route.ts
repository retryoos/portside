// POST /api/auth/logout. Clear the session cookie. Idempotent: returns 200
// whether or not a session was present.

import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/auth/constants";

export async function POST(): Promise<Response> {
  const response = NextResponse.json({ ok: true });
  response.cookies.set({
    name: SESSION_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
