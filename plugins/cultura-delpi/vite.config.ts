import path from "node:path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "cultura-delpi",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
  ],

  resolve: {
    alias: {
      "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
    },
  },

  base: "/apps/cultura-delpi/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
