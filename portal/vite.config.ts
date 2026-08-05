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
          if (id.includes("/node_modules/lucide-react/dist/esm/icons/")) {
            const fileName = id.split("/").pop() ?? "";
            const first = fileName.charAt(0).toLowerCase();

            if (first >= "a" && first <= "f") return "lucide-icons-a-f";
            if (first >= "g" && first <= "m") return "lucide-icons-g-m";
            if (first >= "n" && first <= "s") return "lucide-icons-n-s";
            return "lucide-icons-t-z";
          }

          if (id.includes("/node_modules/lucide-react/")) {
            return "lucide-core";
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