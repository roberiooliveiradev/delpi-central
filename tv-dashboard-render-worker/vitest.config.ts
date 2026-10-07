import { defineConfig } from "vitest/config";

// Server-side (node) tests only — the render page bundle is exercised by the
// browser integration test, not jsdom.
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    environment: "node",
  },
});
