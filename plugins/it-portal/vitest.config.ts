import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { pluginUiTestAliases, reactResolveAliases } from "../vite/federation.shared";

const pluginDir = path.resolve(__dirname);
const pluginsRoot = path.resolve(pluginDir, "..");

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    testTimeout: 20_000,
  },
  server: {
    /* Alias @delpi/plugin-ui aponta para sibling; Vite nega ?raw fora do root. */
    fs: {
      allow: [pluginDir, path.join(pluginsRoot, "plugin-ui")],
    },
  },
  resolve: {
    alias: [
      /* Import relativo `../assets/logoDelpiMark.svg?raw` do kit: casar o especificador inteiro. */
      {
        find: /^.*logoDelpiMark\.svg\?raw$/,
        replacement: path.resolve(pluginDir, "src/test-stubs/logoDelpiMark.svg.raw.js"),
      },
      ...pluginUiTestAliases(pluginDir),
      ...Object.entries(reactResolveAliases(pluginDir)).map(
        ([find, replacement]) => ({ find, replacement }),
      ),
      /* plugin-ui importa lucide-react; resolve contra o node_modules local. */
      {
        find: "lucide-react",
        replacement: path.resolve(pluginDir, "node_modules/lucide-react"),
      },
    ],
  },
});
