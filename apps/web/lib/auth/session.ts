// Session verification for the first-party auth bridge.
//
// The session cookie now carries the BACKEND's HS256 JWT (minted by the API's
// /auth/login and /auth/signup). This module verifies that JWT so the same
// helper works in three places: the Edge middleware gate, the /api/auth/me
// account lookup, and the /api/auth/token bearer passthrough. Verification is
// constant-time and rejects any token with a bad signature, a tampered
// payload, or an `exp` in the past.
//
// The signing secret is shared with the API (APP_JWT_SECRET). In dev both
// sides fall back to the same insecure default so `npm run dev` + the local
// API work with zero config; production MUST set APP_JWT_SECRET on both.
//
// Web Crypto (not Node `crypto`) so this runs unchanged in the Edge runtime.

export interface Session {
  sub: string; // backend user id (uuid hex)
  name: string; // display name for the account chip
  email: string | null; // login email
  iat: number; // issued-at, unix seconds
  exp: number; // expires-at, unix seconds
}

// Mirrors the API's dev default in laytimely_api/settings.py so local dev
// verifies tokens with no env wiring. Any real deploy MUST set APP_JWT_SECRET.
const DEV_FALLBACK_SECRET = "dev-insecure-app-jwt-secret-change-me";
let warned = false;

function getSecret(): string {
  const secret = process.env.APP_JWT_SECRET;
  if (secret && secret.length >= 16) return secret;
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "[auth] APP_JWT_SECRET is unset or too short in production. " +
        "Set it (matching the API) to a random 32+ char value.",
    );
  }
  if (!warned) {
    warned = true;
    // eslint-disable-next-line no-console
    console.warn(
      "[auth] APP_JWT_SECRET unset; using the dev fallback. Set it (matching " +
        "the API) before deploying.",
    );
  }
  return DEV_FALLBACK_SECRET;
}

function base64urlDecode(s: string): Uint8Array {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function base64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function hmac(body: string): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(getSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(body),
  );
  return new Uint8Array(sig);
}

function safeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

// Verify a standard compact HS256 JWT (header.payload.signature) against the
// shared secret. Returns the normalised Session on success, null otherwise.
export async function verifySession(
  token: string | undefined,
): Promise<Session | null> {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [header, payload, signature] = parts as [string, string, string];

  let givenSig: Uint8Array;
  try {
    givenSig = base64urlDecode(signature);
  } catch {
    return null;
  }
  const expectedSig = await hmac(`${header}.${payload}`);
  if (!safeEqual(givenSig, expectedSig)) return null;

  let claims: {
    sub?: unknown;
    name?: unknown;
    email?: unknown;
    iat?: unknown;
    exp?: unknown;
    alg?: unknown;
  };
  try {
    claims = JSON.parse(new TextDecoder().decode(base64urlDecode(payload)));
  } catch {
    return null;
  }

  if (
    typeof claims.sub !== "string" ||
    typeof claims.exp !== "number" ||
    typeof claims.iat !== "number"
  ) {
    return null;
  }
  if (claims.exp < Math.floor(Date.now() / 1000)) return null;

  const email = typeof claims.email === "string" ? claims.email : null;
  const name =
    typeof claims.name === "string" && claims.name.trim()
      ? claims.name
      : (email?.split("@")[0] ?? "Account");

  return { sub: claims.sub, name, email, iat: claims.iat, exp: claims.exp };
}

// Re-exported so callers needing to encode a base64url value (none today) have
// it; kept tiny to avoid a second util module.
export { base64urlEncode };
