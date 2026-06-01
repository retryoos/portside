// Vitest config (review #13). Path alias mirrors tsconfig.json so the
// ``@/lib/...`` imports the same modules at test time as at build time.
// Node test environment (no jsdom), every helper covered here is pure
// JS, no React, no DOM. When component tests land, add jsdom + RTL.

import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("./", import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      "@": root,
    },
  },
  test: {
    environment: "node",
    include: ["**/*.test.ts"],
    exclude: ["node_modules", ".next"],
  },
});
