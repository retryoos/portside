// Centralised feature-flag reader (review #16). Reads ``NEXT_PUBLIC_*``
// env vars at module import (Next.js inlines them at build time) and
// exposes a typed surface so components don't have to think about truthy
// string parsing or env var naming. Add a new flag here when a new
// surface ships behind one — never reach for ``process.env`` directly in
// a component.

function readBool(name: string): boolean {
  if (typeof process === "undefined") return false;
  const raw = process.env[name];
  if (!raw) return false;
  const lower = raw.toLowerCase();
  return lower === "1" || lower === "true" || lower === "yes" || lower === "on";
}

export const flags = {
  /** Show the workspace switcher chip + hide the personal workspace name in
   *  UI copy. Off by default until a real workspace UI ships. */
  workspacesUi: readBool("NEXT_PUBLIC_WORKSPACES_UI"),
};
