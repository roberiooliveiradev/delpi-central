import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "inspecoes-entrada",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
  ],

  base: "/apps/inspecoes-entrada/",

  server: {
    port: 5173,
    proxy: {
      "/apps/api-delpi": {
        target: "http://localhost",
        changeOrigin: true,
      },
    },
  },

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
