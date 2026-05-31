// GET /api/auth/token. Returns the bearer token the browser should send to the
// backend as `Authorization: Bearer <token>`, or 401 when signed out.
//
// The session cookie is HttpOnly, so client JS can't read it directly; this
// same-origin server route is the only thing that can. It returns whatever the
// validated cookie carries: today that's the stub HMAC token (the API ignores
// it while DEV_AUTH=1), and after the Cognito swap (notes/first_customer_
// checklist.md §4) it's the Cognito IdToken the API verifies. The API client
// (lib/api.ts) keeps working unchanged across that swap.

import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/auth/constants";
import { verifySession } from "@/lib/auth/session";

export async function GET(): Promise<Response> {
  const jar = await cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  const session = await verifySession(token);
  if (!session || !token) {
    return NextResponse.json({ token: null }, { status: 401 });
  }
  return NextResponse.json({ token });
}
