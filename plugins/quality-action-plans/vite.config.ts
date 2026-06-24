import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "quality-action-plans",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
  ],

  base: "/apps/quality-action-plans/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
