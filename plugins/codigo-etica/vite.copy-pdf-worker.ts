import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import type { Plugin } from "vite";

const require = createRequire(import.meta.url);

/** Copia o worker do PDF.js como `.js` (MIME padrão application/javascript). */
export function copyPdfWorkerJsPlugin(): Plugin {
  const copy = () => {
    const src = require.resolve("pdfjs-dist/build/pdf.worker.min.mjs");
    const destDir = path.resolve(__dirname, "public/assets");
    mkdirSync(destDir, { recursive: true });
    copyFileSync(src, path.join(destDir, "pdf.worker.min.js"));
  };

  return {
    name: "copy-pdf-worker-js",
    buildStart() {
      copy();
    },
    configureServer() {
      copy();
    },
  };
}
