// Cover the truthy-string parsing in lib/flags (review #13/#16). Important
// because environment variables come in many shapes and a regression here
// silently disables a feature gate.

import { describe, expect, it, vi } from "vitest";

async function reload(value: string | undefined): Promise<boolean> {
  vi.resetModules();
  if (value === undefined) {
    delete process.env.NEXT_PUBLIC_WORKSPACES_UI;
  } else {
    process.env.NEXT_PUBLIC_WORKSPACES_UI = value;
  }
  const mod = await import("./flags");
  return mod.flags.workspacesUi;
}

describe("flags.workspacesUi env parsing", () => {
  it.each(["1", "true", "TRUE", "yes", "on"])(
    "is true for %s",
    async (value) => {
      expect(await reload(value)).toBe(true);
    },
  );

  it.each([undefined, "", "0", "false", "off", "no", "anything-else"])(
    "is false for %s",
    async (value) => {
      expect(await reload(value)).toBe(false);
    },
  );
});
