import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import path from "node:path";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "tv-dashboard",
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
      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
      ...reactResolveAliases(__dirname),
    },
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/tv-dashboard/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
