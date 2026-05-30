# 21 - Authentication stub (pre-Cognito C2)

> The shipped form of the early half of [20 - Track C, C2](20-production-frontend-roman.md).
> An HMAC-signed cookie session bound to a hardcoded `admin / admin` credential
> check. Engineered so the eventual swap to AWS Cognito is a single-file change.
> This doc is the build-from-scratch reference: contracts, flows, configuration,
> security properties, and the two follow-on changes (Cognito swap, registration).

---

## 1. Scope

In:

- A `/login` page that is the only public web surface.
- Edge middleware that redirects every other route to `/login` when the session
  cookie is missing or invalid.
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
- A stateless, HMAC-signed session cookie with an 8h lifetime.
- An account chip in the top nav with a Sign out menu.
- Deep-link survival through the login round trip via `?next=`.

Out, deferred to follow-on PRs (see [Section 9](#9-extension-points)):

- Registration, password reset, "remember me", account lockout, rate limiting.
- Real identity provider (Cognito) and a real user store (Aurora Postgres,
  see [18 - Track A, A1/A2](18-production-platform-dkall.md)).
- JWT propagation to the FastAPI backend (planned as the existing C2 brief: the
  same cookie envelope, but carrying a Cognito ID token whose `sub` becomes the
  scope key on backend list / read / delete endpoints).

The intent is that the contracts in this doc (cookie name, session payload
shape, middleware redirect rules, login API request/response) stay stable when
the stub is replaced. Only the verifier function and the token format change.

---

## 2. File inventory

Every file in this feature, with its single responsibility.

| Path | New / changed | Responsibility |
| --- | --- | --- |
| [apps/web/lib/auth/constants.ts](../apps/web/lib/auth/constants.ts) | new | Cookie name, session TTL, login + post-login paths, `?next=` key. One source of truth. |
| [apps/web/lib/auth/credentials.ts](../apps/web/lib/auth/credentials.ts) | new | The stub credential check. The only place that knows `admin / admin` is valid. Swap target for Cognito InitiateAuth. |
| [apps/web/lib/auth/session.ts](../apps/web/lib/auth/session.ts) | new | Stateless session: HMAC-SHA256 sign / verify over a JSON payload, encoded as `base64url(body).base64url(sig)`. Web Crypto so it runs in both Node and Edge runtimes. |
| [apps/web/app/api/auth/login/route.ts](../apps/web/app/api/auth/login/route.ts) | new | `POST` handler. Verifies credentials, mints the cookie, returns the user. |
| [apps/web/app/api/auth/logout/route.ts](../apps/web/app/api/auth/logout/route.ts) | new | `POST` handler. Clears the cookie. Idempotent. |
| [apps/web/app/api/auth/me/route.ts](../apps/web/app/api/auth/me/route.ts) | new | `GET` handler. Returns the current user or 401. |
| [apps/web/middleware.ts](../apps/web/middleware.ts) | new | Edge middleware. Gates every route except `/login` and `/api/auth/*`. |
| [apps/web/app/login/page.tsx](../apps/web/app/login/page.tsx) | new | Server shell. Parses + sanitises `?next=`, renders the form. |
| [apps/web/app/login/LoginForm.tsx](../apps/web/app/login/LoginForm.tsx) | new | Client form. State, submission, error surfacing, post-login redirect. |
| [apps/web/components/TopNav.tsx](../apps/web/components/TopNav.tsx) | changed | Replaced the static "Claims desk" pill with an account chip + dropdown (signed-in name + Sign out). |

No other file was touched. The API client in [apps/web/lib/api.ts](../apps/web/lib/api.ts)
is untouched; the FastAPI backend is untouched. Backend authentication is the
Cognito work in [18 - Track A, A2](18-production-platform-dkall.md) and is
deliberately not coupled to this stub.

---

## 3. Wire contracts

All three routes are JSON in / JSON out. Cookies are set via response headers,
not by client JavaScript (the cookie is `HttpOnly`).

### `POST /api/auth/login`

Request body:

```json
{ "username": "admin", "password": "admin" }
```

Responses:

| Status | Body | Side effect |
| --- | --- | --- |
| 200 | `{ "user": { "sub": "admin", "name": "Admin" } }` | `Set-Cookie: portside_session=<token>; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800` (Secure in production) |
| 400 | `{ "error": "Username and password are required." }` | none |
| 400 | `{ "error": "Invalid request body" }` (JSON parse failed) | none |
| 401 | `{ "error": "Invalid username or password." }` | none |

The 401 message is intentionally generic. The username is not echoed back and
the message does not distinguish "no such user" from "wrong password". This
keeps the door closed on enumeration even though, today, there is only one
user.

### `POST /api/auth/logout`

Empty body. Always returns 200 `{ "ok": true }` with `Set-Cookie:
portside_session=; Max-Age=0; ...`. Safe to call when no session exists.

### `GET /api/auth/me`

| Status | Body |
| --- | --- |
| 200 | `{ "user": { "sub": "admin", "name": "Admin" } }` |
| 401 | `{ "user": null }` |

Used by the account chip to render the signed-in display name. Cheap; no server
state lookup.

---

## 4. Session token format

The token in the cookie is shaped like a stripped-down JWS:

```
base64url(JSON(payload)) "." base64url(HMAC-SHA256(body, AUTH_SECRET))
```

Payload (`Session` in [session.ts](../apps/web/lib/auth/session.ts)):

```ts
interface Session {
  sub: string;  // user id; "admin" today, Cognito `sub` (UUID) tomorrow
  name: string; // display name for the account chip
  iat: number;  // unix seconds, issued-at
  exp: number;  // unix seconds, expires-at (iat + 8h)
}
```

Verification rules (any failure returns `null`, treated as unauthenticated):

1. Token must contain exactly one `.` with non-empty body and signature halves.
2. The signature, base64url-decoded, must equal `HMAC-SHA256(body, secret)`
   under a **constant-time** byte compare.
3. The decoded payload must have all four fields of the right type.
4. `exp` must be in the future.

There is no server-side session store. The cookie is the whole session. This
mirrors what Cognito gives you (a self-validating ID token), so the verifier
swap is structurally identical.

### Cookie attributes

| Attribute | Value | Why |
| --- | --- | --- |
| `Name` | `portside_session` | Constant in `lib/auth/constants.ts` |
| `HttpOnly` | yes | Inaccessible to `document.cookie`, so XSS cannot exfiltrate the session |
| `SameSite` | `Lax` | Sent on top-level navigation, blocked on cross-site sub-requests; combined with POST-only login it neutralises CSRF for this surface |
| `Secure` | `process.env.NODE_ENV === "production"` | HTTPS-only outside local dev |
| `Path` | `/` | Sent on every route |
| `Max-Age` | `28800` (8h) | Equals the `exp` claim; cookie and payload expire together |

---

## 5. Sequence flows

ASCII ladder diagrams. `MW` is the Edge middleware. `B` is the browser.

### 5.1 First-visit login

```
B                          Next.js (MW)              Route handler
│  GET /                       │                          │
│ ────────────────────────────▶│                          │
│                              │ no cookie → 302          │
│        Location: /login?next=%2F                        │
│ ◀────────────────────────────│                          │
│  GET /login?next=%2F         │                          │
│ ────────────────────────────▶│                          │
│                              │ allow (login route)      │
│            renders login page                           │
│ ◀────────────────────────────│                          │
│  POST /api/auth/login        │                          │
│    { "admin", "admin" } ───▶ │ allow (api/auth)         │
│                              │ ───────────────────────▶ │
│                              │      verifyCredentials() │
│                              │ ◀ Set-Cookie: portside_session=...
│ ◀─────────────────────────── 200 { user }                │
│  router.replace("/")         │                          │
│ ────────────────────────────▶│ cookie ok → allow        │
│        server redirect to /cases                         │
│ ◀────────────────────────────│                          │
```

### 5.2 Deep-link survival

A signed-out user clicks `/cases/v_abc123`. The middleware preserves the path
in `?next=`. After login, `LoginForm` calls `router.replace(next ?? "/cases")`,
so they land back on the deep link, not the dashboard.

The `?next=` value is sanitised in [login/page.tsx](../apps/web/app/login/page.tsx)
before being handed to the form: it must start with `/` and must not start with
`//`. That blocks `?next=//evil.com`-style open-redirect attempts.

### 5.3 Authenticated page load

```
B                          MW                       Page
│  GET /cases                  │                       │
│ ────────────────────────────▶│ verifySession() OK    │
│                              │ ────────────────────▶ │
│ ◀────────────────────── HTML + cookie unchanged      │
│  fetch /api/auth/me  (from TopNav on mount)          │
│ ────────────────────────────▶│ allow (api/auth)      │
│ ◀────────────────────── 200 { user: { name: "Admin" }}
│  account chip renders "A · Admin"                    │
```

### 5.4 Logout

```
B                          MW                       Logout handler
│  click "Sign out"            │                          │
│  POST /api/auth/logout       │                          │
│ ────────────────────────────▶│ allow                    │
│                              │ ────────────────────────▶│
│ ◀──── 200 + Set-Cookie: portside_session=; Max-Age=0    │
│  router.replace("/login")    │                          │
│ ────────────────────────────▶│ no cookie → allow        │
│            renders login page                           │
```

### 5.5 `/login` while already signed in

The middleware special-cases `/login`: if the cookie is valid, it redirects to
`POST_LOGIN_PATH` (`/cases`) instead of rendering the form. There is no point
re-signing in, and a confused user staring at the form would otherwise have to
hit Back.

---

## 6. Configuration

### Required for production

| Env var | Where it's read | What it does |
| --- | --- | --- |
| `AUTH_SECRET` | [lib/auth/session.ts](../apps/web/lib/auth/session.ts) `getSecret()` | HMAC key for signing and verifying the session token. Must be at least 16 characters; 32+ random bytes recommended. Generate with `openssl rand -hex 32`. |
| `NODE_ENV=production` | login + logout route handlers | Flips the cookie `Secure` flag on, so the cookie is HTTPS-only. |

If `AUTH_SECRET` is unset or shorter than 16 characters, the code falls back to
a hardcoded dev string and prints one warning to the server console. This is
fine for local dev. Deployments that ship the fallback are insecure: anyone
who knows the string can mint a valid cookie.

### Local dev

No config required. `npm run dev` works out of the box; the dev fallback secret
is used and the cookie is set without `Secure` so it works on `http://localhost`.

To suppress the warning locally, drop a single line in `apps/web/.env`:

```
AUTH_SECRET=local-dev-secret-please-do-not-deploy-this
```

---

## 7. Security properties

What this design guarantees, and what it deliberately does not.

Guaranteed:

- **No tokens in JavaScript-reachable storage.** The session is `HttpOnly`, so
  an XSS bug cannot exfiltrate it. (XSS can still act as the user inside the
  page, but not steal the session for offline reuse.)
- **No credential check on the client.** The browser POSTs raw credentials to
  the server; the verifier function decides. Replacing the verifier is a server
  change with no client deploy.
- **CSRF mitigated on this surface.** `SameSite=Lax` blocks cross-site POSTs.
  The login endpoint is POST-only with a JSON body, so the classic form-POST
  CSRF vector does not apply.
- **Tampered tokens are rejected.** Any change to the payload invalidates the
  HMAC. Constant-time comparison of the signature blocks timing-based forgery.
- **Open-redirect blocked.** `?next=` is allowlist-validated to same-origin paths.
- **Username enumeration not enabled.** The 401 message is the same regardless
  of which field was wrong.
- **Stateless.** The server holds no session table. A process restart does not
  log everyone out, and there is no shared store to compromise.

Not yet guaranteed (because this is a stub):

- **No rate limiting** on `POST /api/auth/login`. A real backend will need it
  (the App Runner / API Gateway layer in [19 - Track B, P9](19-production-reasoning-panos.md)
  is the natural home).
- **No revocation.** A signed cookie remains valid until `exp`. With Cognito
  the same is true; revocation moves to the IdP. For the stub it does not
  matter because there is one fixed user.
- **No password hashing or store.** There is one hardcoded password compared
  in constant time, which is the right shape for a stub but is not a record
  store. Registration adds that, see [Section 9](#9-extension-points).

---

## 8. Reproducing from scratch

Order of operations. Each step is independent of the next so you can pause and
verify between.

1. Add [apps/web/lib/auth/constants.ts](../apps/web/lib/auth/constants.ts).
   Export `SESSION_COOKIE`, `SESSION_MAX_AGE_SECONDS` (8h), `LOGIN_PATH`,
   `POST_LOGIN_PATH`, `NEXT_PARAM`.
2. Add [apps/web/lib/auth/session.ts](../apps/web/lib/auth/session.ts).
   Use Web Crypto (`crypto.subtle.importKey` + `sign`) for HMAC-SHA256 so the
   module loads in both Edge and Node runtimes. Export `Session`, `signSession`,
   `verifySession`. Implement constant-time signature comparison. Read the
   secret from `AUTH_SECRET` with a warned dev fallback.
3. Add [apps/web/lib/auth/credentials.ts](../apps/web/lib/auth/credentials.ts).
   Export `verifyCredentials(username, password) -> StubUser | null`. Compare
   the password in constant time even with one record (matching the eventual
   real-verifier shape costs nothing).
4. Add the three route handlers under
   [apps/web/app/api/auth/](../apps/web/app/api/auth/):
   - `login/route.ts`: POST, JSON in, verify creds, mint cookie via
     `NextResponse.cookies.set(...)` so it ships on this same response.
   - `logout/route.ts`: POST, clear the cookie with `maxAge: 0`.
   - `me/route.ts`: GET, read `cookies()` and call `verifySession()`.
5. Add [apps/web/middleware.ts](../apps/web/middleware.ts). Read the cookie,
   call `verifySession()`, then:
   - `/login` + session  → redirect to `POST_LOGIN_PATH`.
   - `/login` + no session → allow.
   - other + no session → redirect to `/login?next=<original>`.
   - other + session → allow.
   Use a matcher that excludes `api/auth`, `_next/static`, `_next/image`,
   `favicon.ico`, `logo.png`, and any path with a dot (static assets).
6. Add [apps/web/app/login/page.tsx](../apps/web/app/login/page.tsx). Server
   component. `async` because Next 15 `searchParams` is a `Promise`. Sanitise
   `next` (must start with `/`, must not start with `//`) and pass it to the
   form. Layout matches DESIGN.md: gradient orbs, soft white card, Papership.Ai
   wordmark above the card.
7. Add [apps/web/app/login/LoginForm.tsx](../apps/web/app/login/LoginForm.tsx).
   Client component. Controlled inputs, accessible labels (`htmlFor` +
   `useId`), `aria-invalid` + `aria-describedby` on error, `role="alert"` on
   the error message, autofocus on the username field. POST to
   `/api/auth/login`, surface the server's `error` field on failure, on success
   call `router.replace(next ?? "/cases")` then `router.refresh()` so the
   server layout re-reads the new cookie.
8. Edit [apps/web/components/TopNav.tsx](../apps/web/components/TopNav.tsx).
   Replace the static "Claims desk" chip with an `AccountMenu` component.
   `AccountMenu` fetches `/api/auth/me` on mount, renders an initials avatar +
   display name, opens a dropdown on click with the user info and a Sign out
   button. Close the dropdown on outside-click and Escape.

Verify with `npm run typecheck`. The whole feature is ~280 lines of TS +
~120 lines of TSX, no new runtime deps.

---

## 9. Extension points

### 9.1 Swap to AWS Cognito (planned for C2 second half)

The point of this design is that the swap is small. The cookie name, the
middleware logic, the `/login` UI, the account chip, and the post-login
redirect all stay. What changes:

- [credentials.ts](../apps/web/lib/auth/credentials.ts) is replaced by a call
  to Cognito `InitiateAuth` (USER_PASSWORD_AUTH or USER_SRP_AUTH). The user
  POSTs username + password to `/api/auth/login` as today; the handler proxies
  to Cognito and receives the ID token.
- [session.ts](../apps/web/lib/auth/session.ts) is replaced by a JWKS-backed
  JWT verifier (`jose`'s `createRemoteJWKSet` + `jwtVerify`). The cookie
  carries the Cognito ID token directly. The middleware still calls
  `verifySession(token)` and still gets `{ sub, name, iat, exp }` back; the
  shape stays.
- The backend ([18 - Track A, A2](18-production-platform-dkall.md)) starts
  reading the same cookie / Bearer header and verifying against the same JWKS,
  so `sub` becomes the owner-scope key on `/voyages` reads, writes, and
  deletes.

Until Cognito is provisioned, swap targets can be stubbed with the existing
`DEV_AUTH=1` pattern described in [20 - Track C](20-production-frontend-roman.md).

### 9.2 Registration (next user-visible feature)

Add, in this order, each as its own PR:

1. A user table behind the `VoyageStore`-style protocol that backs A1 (likely
   `users(id PK, email UNIQUE, password_hash, display_name, created_at)`).
2. `lib/auth/passwords.ts`: hash with argon2id (Node-side; the route handler
   stays Node runtime, not Edge). Comparison with `argon2.verify`.
3. `POST /api/auth/register`: validate email + password strength
   server-side, hash, insert, mint a session, return the same `{ user }` shape
   as login. The first user could remain seeded as `admin / admin` for
   continuity.
4. `lib/auth/credentials.ts`: replace the hardcoded check with a store lookup
   plus an argon2 verify. The function signature stays
   `(username, password) -> User | null`.
5. `/register` page mirroring the `/login` shell. The middleware matcher must
   allowlist it the same way `/login` is allowlisted (extend the route check
   in the middleware, not the regex).
6. A "Forgot password" link + reset flow as a separate, later PR. Out of scope
   here.

The session cookie, the middleware, the account chip, and the login flow do
not change.

### 9.3 Backend JWT propagation

Once Cognito lands, the API client in [lib/api.ts](../apps/web/lib/api.ts)
needs to attach the ID token on every request. Two safe shapes:

- **Bearer header.** Read the token from a same-origin `/api/auth/token`
  endpoint (server reads the cookie, returns the raw JWT), cache for its
  lifetime, attach as `Authorization: Bearer ...`. The token itself never
  touches `document.cookie` or `localStorage`.
- **Cookie forwarding.** If the Next.js host and the FastAPI host share a
  parent domain, set the cookie's `Domain` attribute and let it ride to the
  API automatically. Simpler, but couples deployment topology.

The first shape is the default until there is a reason to prefer the second.

---

## 10. Verify by hand

Each item is a 10-second check. Run them in order on a fresh browser session
(or an incognito window).

1. `GET /` while signed out → redirects to `/login?next=%2F`.
2. `GET /cases/v_demo` while signed out → redirects to
   `/login?next=%2Fcases%2Fv_demo`.
3. Submit empty form → 400 surfaces inline as
   "Username and password are required."
4. Submit `wrong / wrong` → red inline alert "Invalid username or password.",
   focus stays in the form, no redirect.
5. Submit `admin / admin` while `?next=` was `/cases/v_demo` → lands on
   `/cases/v_demo`, not the dashboard.
6. Reload the page → still signed in.
7. Open DevTools → Application → Cookies. `portside_session` is present,
   `HttpOnly` is checked, `SameSite=Lax`. `Secure` is unchecked locally,
   checked on a production deploy.
8. Open DevTools console and try `document.cookie` → does not list
   `portside_session`.
9. Click the account chip → dropdown opens. Click outside → closes. Press
   `Escape` while open → closes.
10. Click "Sign out" → bounces to `/login`. Hit Back. Cookie is gone,
    middleware re-bounces to `/login`.
11. Open a second tab, sign in, close the tab. Cookie persists; the first
    tab can still navigate the app.
12. Wait > 8h (or temporarily lower `SESSION_MAX_AGE_SECONDS` to 30 to
    test). After expiry, any nav redirects to `/login`. `?next=` carries
    the page you were on.

Failure on any item means the contract documented above has drifted and is
worth fixing before moving on.

---

## 11. Do not touch

- The FastAPI backend. Backend auth is a separate piece of work in
  [18 - Track A, A2](18-production-platform-dkall.md) and must remain
  independent so this UI work can land without waiting on the cloud
  provision in [19 - Track B](19-production-reasoning-panos.md).
- [apps/web/lib/types.ts](../apps/web/lib/types.ts) and
  [apps/api/portside_api/schemas.py](../apps/api/portside_api/schemas.py).
  Both are FROZEN per the track briefs. Auth types live in feature-local
  modules under `lib/auth/`.
- The matcher in [middleware.ts](../apps/web/middleware.ts) when adding a
  second public route. Keep the regex narrow and add named-route checks
  inside the handler, the way `/login` is special-cased today. Broadening
  the matcher is the easy way to accidentally expose a protected page.
