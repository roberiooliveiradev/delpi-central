import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Shell público genérico (fora do portal, sem login). Servido pelo gateway em /p/.
// Cada app registra suas páginas públicas no shell (ver src/shell/registry.ts).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
    },
  },
  base: "/p/",
  build: {
    target: "esnext",
  },
});
