/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import path from "node:path";

import {
  pluginUiTestAliases,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  resolve: {
    alias: [
      {
        find: "lucide-react",
        replacement: path.resolve(__dirname, "node_modules/lucide-react"),
      },
      ...pluginUiTestAliases(__dirname),
      ...Object.entries(reactResolveAliases(__dirname)).map(
        ([find, replacement]) => ({ find, replacement }),
      ),
    ],
    dedupe: ["react", "react-dom"],
  },
  test: {
    deps: {
      optimizer: {
        web: {
          enabled: true,
          include: [
            "bpmn-js",
            "bpmn-js-properties-panel",
            "diagram-js",
            "bpmn-moddle",
            "@bpmn-io/properties-panel",
          ],
        },
      },
    },
  },
});
