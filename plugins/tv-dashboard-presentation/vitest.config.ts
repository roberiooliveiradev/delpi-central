import path from "node:path";
import { configDefaults, defineConfig } from "vitest/config";

import { pluginUiTestAliases, reactResolveAliases } from "../vite/federation.shared";

const pluginDir = path.resolve(__dirname);
const pluginsRoot = path.resolve(pluginDir, "..");

export default defineConfig({
  test: {
    environment: "jsdom",
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
  server: {
    /* Alias @delpi/plugin-ui aponta para sibling; Vite nega ?raw fora do root. */
    fs: {
      allow: [pluginDir, path.join(pluginsRoot, "plugin-ui")],
    },
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
