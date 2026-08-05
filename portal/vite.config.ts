import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { portalCacheBustEntryPlugin } from "./vite/cacheBustEntryPlugin";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), portalCacheBustEntryPlugin()],
  resolve: {
    dedupe: ["react", "react-dom"],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // O barrel do lucide e os módulos de ícone se referenciam
          // mutuamente: separá-los cria um ciclo entre chunks que quebra a
          // inicialização do app.
          if (id.includes("/node_modules/lucide-react/")) {
            return "lucide";
          }

          if (
            id.includes("/node_modules/react/") ||
            id.includes("/node_modules/react-dom/") ||
            id.includes("/node_modules/react-router") ||
            id.includes("/node_modules/scheduler/")
          ) {
            return "react-vendor";
          }

          if (
            id.includes("/node_modules/framer-motion/") ||
            id.includes("/node_modules/motion-dom/") ||
            id.includes("/node_modules/motion-utils/")
          ) {
            return "motion-vendor";
          }
        },
      },
    },
  },
  server: {
    host: true,
    allowedHosts: ['portal', 'localhost']
  }
})