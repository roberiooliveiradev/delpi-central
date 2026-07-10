import path from "node:path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

import {
  FEDERATION_SHARED_WITH_DIAGRAM,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "transformometro",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: { ...FEDERATION_SHARED_WITH_DIAGRAM },
    }),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
      "@xyflow/react": path.resolve(__dirname, "node_modules/@xyflow/react"),
    },
    dedupe: ["react", "react-dom", "@xyflow/react"],
  },
  base: "/apps/transformometro/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
