// Auth cross-cutting constants. Single source of truth so the cookie name and
// expiry can't drift between middleware, route handlers, and clients.

export const SESSION_COOKIE = "laytimely_session";

// 8h session is the usual professional default for an internal product surface
// (long enough for a workday, short enough to limit blast radius if a laptop
// walks). Re-tune when real users land.
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 8;

// Where unauthenticated users are sent.
export const LOGIN_PATH = "/login";

// Where authenticated users land after sign-in (and where they're bounced if
// they hit /login while already signed in).
export const POST_LOGIN_PATH = "/cases";

// Query-string key carrying the original destination through the login round
// trip, so a deep link survives the redirect.
export const NEXT_PARAM = "next";
