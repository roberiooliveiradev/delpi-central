import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@delpi/plugin-ui/index": new URL("../plugin-ui/src/index.ts", import.meta.url).pathname,
      "@delpi/plugin-ui": new URL("../plugin-ui/src/index.ts", import.meta.url).pathname,
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
