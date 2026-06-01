// Typed client for the Laytimely API (notes/04-schemas.md §6).

import type {
  AuditEvent,
  CreateInvitationRequest,
  EmailSendError,
  EvidenceChecklist,
  FlaggedEventCitations,
  FlaggedEventStrength,
  InboxAddress,
  LetterEmailRequest,
  MyWorkspaceEntry,
  Perspective,
  PipelineStage,
  SesSendResult,
  VesselSummary,
  VoyageState,
  VoyageSummary,
  WorkspaceError,
  WorkspaceInvitation,
  WorkspaceMember,
} from "./types";

// Trailing slashes are stripped so a NEXT_PUBLIC_API_URL configured with one
// (e.g. "https://api.example.com/") can't produce a double slash in request
// URLs ("https://api.example.com//voyages"), which the backend 404s.
const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

// Bearer token for the backend, fetched from the same-origin token route (the
// session cookie is HttpOnly). Cached briefly so the ~1s voyage poll doesn't
// hit the route every tick. Failure is soft: we send no header and let the API
// decide, so DEV_AUTH=1 mode (which ignores the header) keeps working. After
// the Cognito swap this carries the real IdToken the API verifies.
let _cachedAuth: { value: HeadersInit; at: number } | null = null;
const _AUTH_TTL_MS = 30_000;

async function authHeader(): Promise<HeadersInit> {
  const now = Date.now();
  if (_cachedAuth && now - _cachedAuth.at < _AUTH_TTL_MS) return _cachedAuth.value;
  let value: HeadersInit = {};
  try {
    const res = await fetch("/api/auth/token");
    if (res.ok) {
      const { token } = (await res.json()) as { token?: string | null };
      if (token) value = { Authorization: `Bearer ${token}` };
    }
  } catch {
    // Soft-fail: no header. The API enforces auth on its side.
  }
  _cachedAuth = { value, at: now };
  return value;
}

function invalidateAuth(): void {
  _cachedAuth = null;
}

/**
 * Single entry point for backend calls. Injects the bearer header and, on a
 * 401 (the cached token expired or was rotated), drops the cache and retries
 * once with a fresh token. A second 401 propagates to the caller. 401 is an
 * auth rejection (no side effect ran), so retrying a mutating call is safe.
 */
async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const build = async (): Promise<RequestInit> => ({
    ...init,
    headers: { ...(init.headers as Record<string, string> | undefined), ...(await authHeader()) },
  });
  let res = await fetch(`${API_BASE}${path}`, await build());
  if (res.status === 401) {
    invalidateAuth();
    res = await fetch(`${API_BASE}${path}`, await build());
  }
  return res;
}

export interface VoyageFiles {
  cp: File;
  nor: File;
  sof: File;
}

export async function createVoyage(
  files: VoyageFiles,
  perspective: Perspective,
): Promise<string> {
  const form = new FormData();
  form.append("cp", files.cp);
  form.append("nor", files.nor);
  form.append("sof", files.sof);
  form.append("perspective", perspective);

  const res = await apiFetch(`/voyages`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`createVoyage failed: ${res.status}`);
  const data = (await res.json()) as { voyage_id: string };
  return data.voyage_id;
}

export async function listVoyages(signal?: AbortSignal): Promise<VoyageSummary[]> {
  const res = await apiFetch(`/voyages`, { signal });
  if (!res.ok) throw new Error(`listVoyages failed: ${res.status}`);
  return (await res.json()) as VoyageSummary[];
}

export async function listVessels(signal?: AbortSignal): Promise<VesselSummary[]> {
  const res = await apiFetch(`/vessels`, { signal });
  if (!res.ok) throw new Error(`listVessels failed: ${res.status}`);
  return (await res.json()) as VesselSummary[];
}

export async function getVoyage(
  voyageId: string,
  signal?: AbortSignal,
): Promise<VoyageState> {
  const res = await apiFetch(`/voyages/${voyageId}`, { signal });
  if (!res.ok) throw new Error(`getVoyage failed: ${res.status}`);
  return (await res.json()) as VoyageState;
}

export async function deleteVoyage(voyageId: string): Promise<void> {
  const res = await apiFetch(`/voyages/${voyageId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 404) {
    throw new Error(`deleteVoyage failed: ${res.status}`);
  }
}

/**
 * Send the rendered claim letter via SES. Spec:
 * notes/architecture_weeks_5_to_8.md §1.3. The backend translates SES
 * failures into stable {detail: {code, message}} bodies via EmailErrorCode;
 * callers throw a typed EmailSendError so the toast can be actionable
 * (THROTTLED -> "try again shortly"; UNVERIFIED_RECIPIENT -> "verify the
 * address in SES first"; etc.).
 */
export async function sendClaimLetter(
  voyageId: string,
  body: LetterEmailRequest,
): Promise<SesSendResult> {
  const res = await apiFetch(`/voyages/${voyageId}/letter/email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) return (await res.json()) as SesSendResult;
  // Surface the backend code+message to the caller. The shape is either
  // {detail: {code, message}} for EmailSendError, or {detail: string} for the
  // generic 404/409 branches above.
  let code: EmailSendError["code"] = "UNKNOWN";
  let message = `sendClaimLetter failed: ${res.status}`;
  try {
    const data = await res.json();
    if (data && typeof data.detail === "object" && data.detail) {
      if (typeof data.detail.code === "string") code = data.detail.code;
      if (typeof data.detail.message === "string") message = data.detail.message;
    } else if (typeof data?.detail === "string") {
      message = data.detail;
    }
  } catch {
    // Response wasn't JSON; keep the default message.
  }
  const err: EmailSendError = { code, message, status: res.status };
  throw err;
}

// ---------------------------------------------------------------------------
// Workspaces (W8 + W9, notes/architecture_weeks_5_to_8.md §2.1)
// ---------------------------------------------------------------------------

function _workspaceError(status: number, body: unknown): WorkspaceError {
  let code: WorkspaceError["code"] = "UNKNOWN";
  let message = `request failed: ${status}`;
  if (body && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "object" && detail) {
      const c = (detail as { code?: unknown }).code;
      const m = (detail as { message?: unknown }).message;
      if (typeof c === "string") code = c as WorkspaceError["code"];
      if (typeof m === "string") message = m;
    } else if (typeof detail === "string") {
      message = detail;
    }
  }
  return { code, message, status };
}

async function _parseWorkspaceError(res: Response): Promise<WorkspaceError> {
  try {
    return _workspaceError(res.status, await res.json());
  } catch {
    return { code: "UNKNOWN", message: res.statusText, status: res.status };
  }
}

/** Workspaces the caller is a member of (W8).
 *
 * 401 returns an empty list rather than raising so the
 * ActiveWorkspaceProvider mounted at the root layout does not flood the
 * marketing pages with auth errors. The middleware already redirects
 * unauthed visitors away from authed routes; this is just defensive.
 */
export async function listMyWorkspaces(
  signal?: AbortSignal,
): Promise<MyWorkspaceEntry[]> {
  const res = await apiFetch("/me/workspaces", { signal });
  if (res.status === 401) return [];
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as MyWorkspaceEntry[];
}

/** Admin-only: list every membership row for a workspace (W8). */
export async function listWorkspaceMembers(
  workspaceId: string,
  signal?: AbortSignal,
): Promise<WorkspaceMember[]> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/members`;
  const res = await apiFetch(path, { signal });
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as WorkspaceMember[];
}

/**
 * Admin-only: drop a single membership row (W8). The backend refuses with
 * 409 ``last_owner`` when removing the only owner; the caller surfaces an
 * actionable toast in that case.
 */
export async function removeWorkspaceMember(
  workspaceId: string,
  userSub: string,
): Promise<void> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/members/${encodeURIComponent(userSub)}`;
  const res = await apiFetch(path, { method: "DELETE" });
  if (res.status === 204) return;
  throw await _parseWorkspaceError(res);
}

/** Admin-only: promote or demote a member (review #11). */
export async function changeWorkspaceMemberRole(
  workspaceId: string,
  userSub: string,
  role: WorkspaceMember["role"],
): Promise<WorkspaceMember> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/members/${encodeURIComponent(userSub)}`;
  const res = await apiFetch(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as WorkspaceMember;
}

/** Admin-only: revoke a pending invitation (review #10). */
export async function revokeWorkspaceInvitation(
  workspaceId: string,
  invitationId: number,
): Promise<void> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/invitations/${invitationId}/revoke`;
  const res = await apiFetch(path, { method: "POST" });
  if (res.status === 204) return;
  throw await _parseWorkspaceError(res);
}

/** Admin-only: list pending invitations for a workspace (W9). */
export async function listWorkspaceInvitations(
  workspaceId: string,
  signal?: AbortSignal,
): Promise<WorkspaceInvitation[]> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/invitations`;
  const res = await apiFetch(path, { signal });
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as WorkspaceInvitation[];
}

/** Admin-only: mint a new invitation (W9). */
export async function createWorkspaceInvitation(
  workspaceId: string,
  body: CreateInvitationRequest,
): Promise<WorkspaceInvitation> {
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/invitations`;
  const res = await apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as WorkspaceInvitation;
}

/** Public-ish: accept an invitation token (W9). 410 -> WorkspaceError. */
export async function acceptInvitation(
  token: string,
): Promise<WorkspaceInvitation> {
  const path = `/invitations/${encodeURIComponent(token)}/accept`;
  const res = await apiFetch(path, { method: "POST" });
  if (!res.ok) throw await _parseWorkspaceError(res);
  return (await res.json()) as WorkspaceInvitation;
}

/**
 * Forward-to inbox address for the workspace (W7,
 * notes/architecture_weeks_5_to_8.md §2.3). Backend route:
 * GET /workspaces/{id}/inbox-address. Admin-only; 403 from the backend
 * means the caller is below admin role on that workspace.
 */
export async function fetchInboxAddress(
  workspaceId: string,
  signal?: AbortSignal,
): Promise<InboxAddress> {
  // The workspace_id may include a colon ("personal:<sub>"); URL-encode so
  // the route layer receives the slug intact.
  const path = `/workspaces/${encodeURIComponent(workspaceId)}/inbox-address`;
  const res = await apiFetch(path, { signal });
  if (!res.ok) throw new Error(`fetchInboxAddress failed: ${res.status}`);
  return (await res.json()) as InboxAddress;
}

/**
 * Recent audit events for the caller (W6,
 * notes/architecture_weeks_5_to_8.md §2.2). Backend route: GET /audit; the
 * server clamps ``limit`` to [1, 500]. Newest-first by ``at``.
 */
export async function listAuditEvents(
  limit = 100,
  signal?: AbortSignal,
): Promise<AuditEvent[]> {
  const url = `/audit?limit=${encodeURIComponent(String(limit))}`;
  const res = await apiFetch(url, { signal });
  if (!res.ok) throw new Error(`listAuditEvents failed: ${res.status}`);
  return (await res.json()) as AuditEvent[];
}

/**
 * Verified legal authorities per flagged event (W5,
 * notes/architecture_weeks_5_to_8.md §1.6). Backend route:
 * GET /voyages/{id}/citations. Returns null when the dispute analysis has
 * not landed yet (409) or the voyage is unknown (404). An empty list means
 * the picker ran but no candidate survived verification for any event.
 */
export async function fetchCitations(
  voyageId: string,
  signal?: AbortSignal,
): Promise<FlaggedEventCitations[] | null> {
  const res = await apiFetch(`/voyages/${voyageId}/citations`, { signal });
  if (res.status === 404 || res.status === 409) return null;
  if (!res.ok) throw new Error(`fetchCitations failed: ${res.status}`);
  return (await res.json()) as FlaggedEventCitations[];
}

/**
 * Per-event claim-strength sub-score panels (W4,
 * notes/architecture_weeks_5_to_8.md §1.5). Backend route:
 * GET /voyages/{id}/strengths. Returns null when the dispute analysis has
 * not landed yet (409) or the voyage is unknown (404).
 */
export async function fetchClaimStrengths(
  voyageId: string,
  signal?: AbortSignal,
): Promise<FlaggedEventStrength[] | null> {
  const res = await apiFetch(`/voyages/${voyageId}/strengths`, { signal });
  if (res.status === 404 || res.status === 409) return null;
  if (!res.ok) throw new Error(`fetchClaimStrengths failed: ${res.status}`);
  return (await res.json()) as FlaggedEventStrength[];
}

/**
 * Recipient-facing evidence checklist (W3,
 * notes/architecture_weeks_5_to_8.md §1.4). Backend route:
 * GET /voyages/{id}/evidence-checklist. Returns null when the dispute
 * analysis has not landed yet (409) or the voyage is unknown (404) so the
 * tab can render an empty/loading state instead of an error.
 */
export async function fetchEvidenceChecklist(
  voyageId: string,
  signal?: AbortSignal,
): Promise<EvidenceChecklist | null> {
  const res = await apiFetch(`/voyages/${voyageId}/evidence-checklist`, { signal });
  if (res.status === 404 || res.status === 409) return null;
  if (!res.ok) throw new Error(`fetchEvidenceChecklist failed: ${res.status}`);
  return (await res.json()) as EvidenceChecklist;
}

/**
 * Download the three-sheet laytime workbook (Calculation / Summary / Letter)
 * for a voyage. Backend route: GET /voyages/{id}/laytime.xlsx, spec in
 * notes/architecture_weeks_5_to_8.md §1.1. 404 = unknown voyage; 409 = the
 * pipeline has not produced laytime yet (caller should surface the message).
 */
export async function downloadLaytimeXlsx(voyageId: string): Promise<Blob> {
  const res = await apiFetch(`/voyages/${voyageId}/laytime.xlsx`);
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail ?? "";
    } catch {
      // Response wasn't JSON; leave detail empty.
    }
    throw new Error(
      `downloadLaytimeXlsx failed: ${res.status}${detail ? ` ${detail}` : ""}`,
    );
  }
  return await res.blob();
}

/** Advance a voyage through the negotiation lifecycle (send/settle/reject/revise). */
export async function setVoyageStatus(
  voyageId: string,
  stage: PipelineStage,
): Promise<VoyageState> {
  const res = await apiFetch(`/voyages/${voyageId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage }),
  });
  if (!res.ok) throw new Error(`setVoyageStatus failed: ${res.status}`);
  return (await res.json()) as VoyageState;
}

// Stages where the pipeline has stopped advancing on its own. Past "done" the
// claim sits in a human-driven negotiation lifecycle (pending/rejected/settled),
// so polling stops there too rather than looping forever.
const TERMINAL: ReadonlySet<string> = new Set([
  "done",
  "error",
  "pending",
  "rejected",
  "settled",
]);

/** setTimeout as a promise that resolves early if the signal aborts. */
function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal?.aborted) return resolve();
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        resolve();
      },
      { once: true },
    );
  });
}

/**
 * Poll until the voyage reaches a terminal stage, calling onUpdate each tick.
 * Pass an AbortSignal and abort it (e.g. on component unmount) to stop the loop;
 * without that the loop would keep hitting the API forever for a voyage that
 * never reaches a terminal stage (a still-processing one).
 */
export async function pollVoyage(
  voyageId: string,
  onUpdate: (state: VoyageState) => void,
  { signal, intervalMs = 1000 }: { signal?: AbortSignal; intervalMs?: number } = {},
): Promise<VoyageState | undefined> {
  for (;;) {
    if (signal?.aborted) return undefined;
    const state = await getVoyage(voyageId, signal);
    onUpdate(state);
    if (TERMINAL.has(state.stage)) return state;
    await delay(intervalMs, signal);
  }
}
