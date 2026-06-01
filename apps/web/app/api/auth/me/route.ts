// GET /api/auth/me. Return the current user's display info, or 401 if signed
// out / expired. The TopNav uses this to render the account chip; client code
// can also poll it after a logout to confirm.

import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/auth/constants";
import { verifySession } from "@/lib/auth/session";

export async function GET(): Promise<Response> {
  const jar = await cookies();
  const session = await verifySession(jar.get(SESSION_COOKIE)?.value);
  if (!session) {
    return NextResponse.json({ user: null }, { status: 401 });
  }
  return NextResponse.json({
    user: { sub: session.sub, name: session.name, email: session.email },
  });
}
