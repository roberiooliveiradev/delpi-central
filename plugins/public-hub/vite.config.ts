import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

// Shell público (/p/) — consome @delpi/plugin-ui via MF; tv-dashboard-presentation bundled.
export default defineConfig({
  plugins: [
    federation({
      name: "public-hub",
      remotes: pluginUiRemote(),
      shared: { ...FEDERATION_SHARED_REACT },
    }),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
      "lucide-react": path.resolve(__dirname, "node_modules/lucide-react"),
      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
    },
    dedupe: ["react", "react-dom", "lucide-react"],
  },
  base: "/p/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
