import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import path from "node:path";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "tv-dashboard",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
  ],
  resolve: {
    alias: {
      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
      "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
    },
  },
  base: "/apps/tv-dashboard/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
