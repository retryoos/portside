// Stateless, HMAC-signed session tokens. Format mirrors a stripped-down JWS:
//
//     base64url(JSON(payload)) "." base64url(HMAC-SHA256(body, secret))
//
// Web Crypto is used so the same helpers run unchanged in the Edge middleware
// runtime (no Node `crypto` import). Verification is constant-time and rejects
// any token whose payload was mutated, whose signature doesn't match the
// current secret, or whose `exp` is in the past.
//
// When the real auth lands (Cognito, notes/20 → C2), this whole module gets
// replaced by JWKS-based JWT verification of the Cognito ID token. The cookie
// shape and the `Session` contract stay; only the verifier changes.

import { SESSION_MAX_AGE_SECONDS } from "./constants";

export interface Session {
  sub: string; // user id (currently the username; later: Cognito `sub`)
  name: string; // display name shown in the account chip
  iat: number; // issued-at, unix seconds
  exp: number; // expires-at, unix seconds
}

// Dev fallback so a fresh `npm run dev` works without env wiring. In any real
// deploy AUTH_SECRET MUST be set; we log a single warning so it's obvious in
// the server console if the fallback is being used.
const DEV_FALLBACK_SECRET = "laytimely-dev-secret-change-me";
let warned = false;

function getSecret(): string {
  const secret = process.env.AUTH_SECRET;
  if (secret && secret.length >= 16) return secret;
  // In production a missing/weak secret lets anyone forge a session cookie, so
  // fail closed rather than silently signing with a public dev value.
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "[auth] AUTH_SECRET is unset or too short in production. " +
        "Set AUTH_SECRET to a random 32+ char value.",
    );
  }
  if (!warned) {
    warned = true;
    // eslint-disable-next-line no-console
    console.warn(
      "[auth] AUTH_SECRET is unset or too short; using a dev fallback. " +
        "Set AUTH_SECRET to a random 32+ char value before deploying.",
    );
  }
  return DEV_FALLBACK_SECRET;
}

function base64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64urlDecode(s: string): Uint8Array {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
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

// Length-independent constant-time compare. Returns false on any length
// mismatch (length is not secret here, but matching the timing shape costs
// nothing and avoids reasoning about it).
function safeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

export async function signSession(claims: {
  sub: string;
  name: string;
}): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const payload: Session = {
    sub: claims.sub,
    name: claims.name,
    iat: now,
    exp: now + SESSION_MAX_AGE_SECONDS,
  };
  const body = base64urlEncode(
    new TextEncoder().encode(JSON.stringify(payload)),
  );
  const sig = base64urlEncode(await hmac(body));
  return `${body}.${sig}`;
}

export async function verifySession(token: string | undefined): Promise<Session | null> {
  if (!token) return null;
  const dot = token.indexOf(".");
  if (dot <= 0 || dot === token.length - 1) return null;
  const body = token.slice(0, dot);
  const givenSig = token.slice(dot + 1);

  let givenBytes: Uint8Array;
  try {
    givenBytes = base64urlDecode(givenSig);
  } catch {
    return null;
  }

  const expectedBytes = await hmac(body);
  if (!safeEqual(givenBytes, expectedBytes)) return null;

  let payload: Session;
  try {
    payload = JSON.parse(new TextDecoder().decode(base64urlDecode(body))) as Session;
  } catch {
    return null;
  }

  if (
    typeof payload.sub !== "string" ||
    typeof payload.name !== "string" ||
    typeof payload.exp !== "number" ||
    typeof payload.iat !== "number"
  ) {
    return null;
  }
  if (payload.exp < Math.floor(Date.now() / 1000)) return null;

  return payload;
}
