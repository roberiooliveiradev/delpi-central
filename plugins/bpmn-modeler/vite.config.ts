/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
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
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
    },
    dedupe: ["react", "react-dom"],
  },
  worker: {
    format: "es",
  },
  base: "/apps/bpmn-modeler/",
  test: {
    exclude: ["e2e/**", "node_modules/**"],
  },
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
