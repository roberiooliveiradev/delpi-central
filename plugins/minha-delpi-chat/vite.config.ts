/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "minha-delpi-chat",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx"
      },
      shared: ["react", "react-dom"]
    })
  ],

  base: "/apps/minha-delpi-chat/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false
  },

  test: {
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
