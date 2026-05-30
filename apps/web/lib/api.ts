// Typed client for the Laytimely API (notes/04-schemas.md §6).

import type {
  Perspective,
  PipelineStage,
  VesselSummary,
  VoyageState,
  VoyageSummary,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

  const res = await fetch(`${API_BASE}/voyages`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`createVoyage failed: ${res.status}`);
  const data = (await res.json()) as { voyage_id: string };
  return data.voyage_id;
}

export async function listVoyages(signal?: AbortSignal): Promise<VoyageSummary[]> {
  const res = await fetch(`${API_BASE}/voyages`, { signal });
  if (!res.ok) throw new Error(`listVoyages failed: ${res.status}`);
  return (await res.json()) as VoyageSummary[];
}

export async function listVessels(signal?: AbortSignal): Promise<VesselSummary[]> {
  const res = await fetch(`${API_BASE}/vessels`, { signal });
  if (!res.ok) throw new Error(`listVessels failed: ${res.status}`);
  return (await res.json()) as VesselSummary[];
}

export async function getVoyage(
  voyageId: string,
  signal?: AbortSignal,
): Promise<VoyageState> {
  const res = await fetch(`${API_BASE}/voyages/${voyageId}`, { signal });
  if (!res.ok) throw new Error(`getVoyage failed: ${res.status}`);
  return (await res.json()) as VoyageState;
}

export async function deleteVoyage(voyageId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/voyages/${voyageId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 404) {
    throw new Error(`deleteVoyage failed: ${res.status}`);
  }
}

/** Advance a voyage through the negotiation lifecycle (send/settle/reject/revise). */
export async function setVoyageStatus(
  voyageId: string,
  stage: PipelineStage,
): Promise<VoyageState> {
  const res = await fetch(`${API_BASE}/voyages/${voyageId}/status`, {
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
