#!/usr/bin/env node
/**
 * Valida patches MF em produção (URLs reais — curl não expande *).
 *
 * Uso:
 *   node plugins/vite/verify-prod-mf-patch.mjs controle-retrabalhos
 *   node plugins/vite/verify-prod-mf-patch.mjs controle-retrabalhos https://minhadelpi.com.br
 */
const appId = process.argv[2];
const baseUrl = (process.argv[3] ?? "https://minhadelpi.com.br").replace(/\/$/, "");

if (!appId) {
  console.error("Uso: node verify-prod-mf-patch.mjs <app-id> [base-url]");
  process.exit(1);
}

const prefix = `${baseUrl}/apps/${appId}/assets`;

async function fetchText(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${url} → HTTP ${res.status}`);
  }
  return res.text();
}

function extractAsset(remoteEntry, pattern) {
  const match = remoteEntry.match(pattern);
  return match?.[1] ?? match?.[0] ?? null;
}

async function main() {
  const remoteEntry = await fetchText(`${prefix}/remoteEntry.js`);
  const expose = extractAsset(remoteEntry, /(__federation_expose_App-[^"]+\.js)/);
  if (!expose) {
    throw new Error("remoteEntry sem __federation_expose_App");
  }

  const exposeCode = await fetchText(`${prefix}/${expose}`);
  const fnImport = extractAsset(exposeCode, /(__federation_fn_import-[^"]+\.js)/);
  const appChunk = extractAsset(exposeCode, /(App-[^"]+\.js)/);

  if (!fnImport || !appChunk) {
    throw new Error(`expose ${expose} sem fn_import ou App chunk`);
  }

  const fnCode = await fetchText(`${prefix}/${fnImport}`);
  const appCode = await fetchText(`${prefix}/${appChunk}`);

  let failed = false;

  if (!fnCode.includes("!globalThis.__DELPI_MF_REACT__")) {
    console.error(`FAIL ${fnImport}: guard !globalThis.__DELPI_MF_REACT__ ausente`);
    failed = true;
  } else {
    console.log(`OK  ${fnImport}: guard presente (${fnCode.length} bytes)`);
  }

  if (!appCode.includes("__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE")) {
    console.error(`FAIL ${appChunk}: fallback dispatcher H ausente`);
    failed = true;
  } else {
    console.log(`OK  ${appChunk}: fallback H presente (${appCode.length} bytes)`);
  }

  if (failed) {
    console.error("\nContainer ainda serve bundle antigo ou build sem patch.");
    console.error("Rebuild: ./infra/scripts/up-prod-sequential.sh --no-cache --fase mfe --build", appId);
    process.exit(1);
  }

  console.log("\nOK: patches MF ativos em produção para", appId);
}

main().catch((err) => {
  console.error("ERRO:", err.message);
  process.exit(1);
});
