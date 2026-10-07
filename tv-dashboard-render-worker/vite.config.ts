import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Bundles the bounded render page. The page imports the SHARED presentation
 * package source — the same component tree the editor/preview/TV use. No
 * second renderer: this only mounts `DesignViewportStage` + `NativeSlideView`.
 */
export default defineConfig({
  root: path.resolve(__dirname, "src/render-page"),
  base: "/render-page/",
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: "@delpi/tv-dashboard-presentation",
        replacement: path.resolve(__dirname, "../plugins/tv-dashboard-presentation/src/index.ts"),
      },
      {
        find: "@delpi/plugin-ui/index",
        replacement: path.resolve(__dirname, "../plugins/plugin-ui/src/index.ts"),
      },
      {
        find: "@delpi/plugin-ui/styles",
        replacement: path.resolve(__dirname, "../plugins/plugin-ui/src/styles.css"),
      },
      {
        find: "@delpi/plugin-ui",
        replacement: path.resolve(__dirname, "../plugins/plugin-ui/src/index.ts"),
      },
      { find: "react", replacement: path.resolve(__dirname, "node_modules/react") },
      { find: "react-dom", replacement: path.resolve(__dirname, "node_modules/react-dom") },
      { find: "react-dom/client", replacement: path.resolve(__dirname, "node_modules/react-dom/client") },
      { find: "lucide-react", replacement: path.resolve(__dirname, "node_modules/lucide-react") },
      // recharts peer dep — declared in this package so Docker builds with
      // --omit=peer on the shared packages still resolve it deterministically.
      { find: "react-is", replacement: path.resolve(__dirname, "node_modules/react-is") },
    ],
    dedupe: ["react", "react-dom", "lucide-react"],
  },
  build: {
    outDir: path.resolve(__dirname, "dist/render-page"),
    emptyOutDir: true,
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
    rollupOptions: {
      // Heavy plugin-ui peers unused by the presentation tree — never resolve.
      external: ["mermaid", "mammoth", "xlsx", "exceljs", "jspdf", "jspdf-autotable", "html-to-image"],
    },
  },
});
