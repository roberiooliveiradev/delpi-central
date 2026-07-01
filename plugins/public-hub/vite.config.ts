import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Shell público genérico (fora do portal, sem login). Servido pelo gateway em /p/.
// Cada app registra suas páginas públicas no shell (ver src/shell/registry.ts).
export default defineConfig({
  plugins: [react()],
  base: "/p/",
  build: {
    target: "esnext",
  },
});
