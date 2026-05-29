// STUB credential check. This is the only place that knows what "valid" means
// today. Swap this single function for a Cognito InitiateAuth call (see
// notes/20-production-frontend-roman.md → C2) and the rest of the auth surface
// (cookie, middleware, login page, account chip) stays untouched.
//
// Hardcoded login: username=admin, password=admin.

export interface StubUser {
  sub: string; // stable user id
  name: string; // display name shown in the account chip
}

// Constant-time compare so this looks like the eventual real verifier even
// though, with one record, timing tells you nothing useful.
function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export function verifyCredentials(
  username: string,
  password: string,
): StubUser | null {
  const u = username.trim().toLowerCase();
  // Comparing the password constant-time avoids leaking length info; the
  // username is treated as public.
  if (u === "admin" && safeEqual(password, "admin")) {
    return { sub: "admin", name: "Admin" };
  }
  return null;
}
