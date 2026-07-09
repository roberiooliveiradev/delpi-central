import path from "node:path";

import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { defineConfig } from "vite";

import { FEDERATION_SHARED_REACT, PLUGIN_UI_DEV_PORT } from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "plugin_ui",
      filename: "remoteEntry.js",
      exposes: {
        "./index": "./src/index.ts",
        "./styles": "./src/styles-entry.ts",
      },
      shared: [...FEDERATION_SHARED_REACT],
    }),
  ],
  resolve: {
    alias: {
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
    },
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/plugin-ui/",
  server: {
    port: PLUGIN_UI_DEV_PORT,
    strictPort: true,
  },
  preview: {
    port: PLUGIN_UI_DEV_PORT,
    strictPort: true,
  },
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
