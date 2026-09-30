/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import path from "node:path";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  pluginUiTestAliases,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig(({ mode }) => {
  const isVitest = mode === "test" || Boolean(process.env.VITEST);

  return {
  plugins: [
    ...(isVitest
      ? []
      : [
          federation({
            name: "bpmn-modeler",
            filename: "remoteEntry.js",
            remotes: pluginUiRemote(),
            exposes: {
              "./App": "./src/bootstrap.tsx",
            },
            shared: { ...FEDERATION_SHARED_REACT },
          }),
          federationReactProxyFixPlugin(),
        ]),
    react(),
  ],
  resolve: {
    alias: [
      ...(isVitest
        ? [
            {
              find: "lucide-react",
              replacement: path.resolve(__dirname, "node_modules/lucide-react"),
            },
          ]
        : []),
      ...(isVitest ? pluginUiTestAliases(__dirname) : []),
      ...Object.entries(reactResolveAliases(__dirname)).map(
        ([find, replacement]) => ({ find, replacement }),
      ),
    ],
    dedupe: ["react", "react-dom"],
  },
  worker: {
    format: "es",
  },
  base: "/apps/bpmn-modeler/",
  test: {
    exclude: ["e2e/**", "node_modules/**"],
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
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
};
});
