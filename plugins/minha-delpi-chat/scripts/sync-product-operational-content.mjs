#!/usr/bin/env node
/**
 * Sync product_operational_content from API → MFE.
 * Strips presentation.routeTitles / routeFraming (MFE is render-only for titles).
 */
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(
  root,
  "../../minha-delpi-ai-api/app/content/pt-BR/assistant/product_operational_content.json",
);
const dst = join(root, "src/content/product_operational_content.json");

copyFileSync(src, dst);
const data = JSON.parse(readFileSync(dst, "utf8"));
if (data.presentation && typeof data.presentation === "object") {
  delete data.presentation.routeTitles;
  delete data.presentation.routeFraming;
}
writeFileSync(dst, `${JSON.stringify(data, null, 2)}\n`, "utf8");
console.log("synced product_operational_content (routeTitles/routeFraming stripped)");
