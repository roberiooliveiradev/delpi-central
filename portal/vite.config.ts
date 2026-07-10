import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { portalCacheBustEntryPlugin } from "./vite/cacheBustEntryPlugin";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), portalCacheBustEntryPlugin()],
  resolve: {
    dedupe: ["react", "react-dom"],
  },
  server: {
    host: true,
    allowedHosts: ['portal', 'localhost']
  }
})