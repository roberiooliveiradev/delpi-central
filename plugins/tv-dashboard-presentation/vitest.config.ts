import path from "node:path";
import { defineConfig } from "vitest/config";

import { pluginUiTestAliases, reactResolveAliases } from "../vite/federation.shared";

const pluginDir = path.resolve(__dirname);

export default defineConfig({
  test: {
    environment: "jsdom",
  },
  resolve: {
    alias: [
      ...pluginUiTestAliases(pluginDir),
      ...Object.entries(reactResolveAliases(pluginDir)).map(([find, replacement]) => ({
        find,
        replacement,
      })),
    ],
  },
});
