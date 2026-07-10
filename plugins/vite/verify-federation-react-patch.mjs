#!/usr/bin/env node
/**
 * Verifica patches de React MF em dist/assets após vite build.
 * Uso: node plugins/vite/verify-federation-react-patch.mjs plugins/dashboard-quality/dist/assets
 */
import fs from "node:fs";
import path from "node:path";

const distDir = process.argv[2];
if (!distDir) {
  console.error("Uso: node verify-federation-react-patch.mjs <dist/assets>");
  process.exit(1);
}

let failed = false;

for (const file of fs.readdirSync(distDir)) {
  if (!file.endsWith(".js")) continue;
  const code = fs.readFileSync(path.join(distDir, file), "utf8");

  if (file.includes("__federation_fn_import")) {
    if (code.includes("Object.assign({},e.default,e)")) {
      console.error(`FAIL ${file}: flattenModule Object.assign ainda presente`);
      failed = true;
    }
    if (!code.includes("__DELPI_MF_REACT__")) {
      console.error(`FAIL ${file}: publish __DELPI_MF_REACT__ ausente`);
      failed = true;
    }
    if (!code.includes("!globalThis.__DELPI_MF_REACT__")) {
      console.error(`FAIL ${file}: publish sem guard !globalThis.__DELPI_MF_REACT__`);
      failed = true;
    }
  }

  if (/(?:^|\/)App-/.test(file) && code.includes('import{r as ') && code.includes('from"./index-')) {
    if (!code.includes("__DELPI_MF_REACT__?.useRef")) {
      console.error(`FAIL ${file}: App chunk sem fallback global no bridge React`);
      failed = true;
    }
  }

  if (
    code.includes("n.useRef=function") &&
    code.includes("export{") &&
    code.includes(" as r}")
  ) {
    if (!code.includes("__DELPI_MF_REACT__")) {
      console.error(`FAIL ${file}: shim React bundled sem redirect global`);
      failed = true;
    }
  }
}

if (failed) {
  process.exit(1);
}

console.log("OK: patches federation React verificados em", distDir);
