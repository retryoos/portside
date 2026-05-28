// Typed client for the Portside API (notes/04-schemas.md §6).

import type { Perspective, VoyageState, VoyageSummary } from "./types";

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

export async function listVoyages(): Promise<VoyageSummary[]> {
  const res = await fetch(`${API_BASE}/voyages`);
  if (!res.ok) throw new Error(`listVoyages failed: ${res.status}`);
  return (await res.json()) as VoyageSummary[];
}

export async function getVoyage(voyageId: string): Promise<VoyageState> {
  const res = await fetch(`${API_BASE}/voyages/${voyageId}`);
  if (!res.ok) throw new Error(`getVoyage failed: ${res.status}`);
  return (await res.json()) as VoyageState;
}

const TERMINAL: ReadonlySet<string> = new Set(["done", "error"]);

/** Poll until the pipeline reaches a terminal stage, calling onUpdate each tick. */
export async function pollVoyage(
  voyageId: string,
  onUpdate: (state: VoyageState) => void,
  intervalMs = 500,
): Promise<VoyageState> {
  for (;;) {
    const state = await getVoyage(voyageId);
    onUpdate(state);
    if (TERMINAL.has(state.stage)) return state;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
