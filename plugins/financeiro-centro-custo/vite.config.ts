/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
  pluginUiTestAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "financeiro-centro-custo",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: { ...FEDERATION_SHARED_REACT },
    }),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
    },
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/financeiro-centro-custo/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    alias: pluginUiTestAliases(__dirname),
  },

});
