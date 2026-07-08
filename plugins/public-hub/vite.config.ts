import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Shell público genérico (fora do portal, sem login). Servido pelo gateway em /p/.
// Cada app registra suas páginas públicas no shell (ver src/shell/registry.ts).
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Pacote compartilhado é compilado do source; sem dedupe o Vite pode
    // puxar react de tv-dashboard-presentation/node_modules → hooks quebram.
    dedupe: ["react", "react-dom", "lucide-react"],
    alias: {
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "lucide-react": path.resolve(__dirname, "node_modules/lucide-react"),
      "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
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
