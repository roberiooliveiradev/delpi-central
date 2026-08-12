#!/usr/bin/env node
/**
 * Gate: public-hub /sign não pode puxar HelpTooltip via MF (createPortal).
 * Uso: node plugins/vite/verify-public-hub-signature-bundle.mjs plugins/public-hub/dist/assets
 */
import fs from "node:fs";
import path from "node:path";

const distDir = process.argv[2];
if (!distDir) {
  console.error("Uso: node verify-public-hub-signature-bundle.mjs <dist/assets>");
  process.exit(1);
}

let failed = false;
let sawSignaturePad = false;

for (const file of fs.readdirSync(distDir)) {
  if (!file.endsWith(".js")) continue;
  const code = fs.readFileSync(path.join(distDir, file), "utf8");
  if (code.includes("HelpTooltip") || code.includes("createPortal indisponível")) {
    console.error(`FAIL ${file}: contém HelpTooltip / erro createPortal (assinatura deve ser bundled)`);
    failed = true;
  }
  if (code.includes("delpi-ui-signature-pad") || code.includes("signature-pad-fullscreen")) {
    sawSignaturePad = true;
  }
}

if (!sawSignaturePad) {
  console.error("FAIL: nenhum chunk com SignaturePad — @delpi/signature-kit não entrou no bundle?");
  failed = true;
}

if (failed) process.exit(1);
console.log("OK: public-hub signature bundled sem HelpTooltip em", distDir);
