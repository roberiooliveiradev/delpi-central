import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "test-microfrontend",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom", "react-router-dom"],
    }),
  ],

  base: "/",

  preview: {
    host: true,
    port: 5175,
    allowedHosts: ["test-microfrontend", "portal", "localhost"],
  },
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});