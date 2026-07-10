import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "api-delpi-console",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
    federationReactProxyFixPlugin(),
  ],
  base: "/apps/api-delpi-console/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
