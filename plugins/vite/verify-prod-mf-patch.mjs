#!/usr/bin/env node
/**
 * Valida patches MF em produção (URLs reais — curl não expande *).
 *
 * Usa ?v= no fetch para contornar Cloudflare immutable stale (cf-cache-status: HIT).
 *
 * Uso:
 *   node plugins/vite/verify-prod-mf-patch.mjs controle-retrabalhos
 *   node plugins/vite/verify-prod-mf-patch.mjs controle-retrabalhos https://minhadelpi.com.br
 */
import { DELPI_MF_PATCH_VERSION } from "./federationPatchVersion.mjs";

const appId = process.argv[2];
const baseUrl = (process.argv[3] ?? "https://minhadelpi.com.br").replace(/\/$/, "");

if (!appId) {
  console.error("Uso: node verify-prod-mf-patch.mjs <app-id> [base-url]");
  process.exit(1);
}

const prefix = `${baseUrl}/apps/${appId}/assets`;
const cacheBust = `v=${DELPI_MF_PATCH_VERSION}&t=${Date.now()}`;

function assetUrl(file) {
  return `${prefix}/${file}?${cacheBust}`;
}

async function fetchText(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${url} → HTTP ${res.status}`);
  }
  const cf = res.headers.get("cf-cache-status");
  if (cf === "HIT") {
    console.warn(`WARN ${url}: cf-cache-status=HIT (purge Cloudflare se o patch falhar)`);
  }
  return res.text();
}

function extractAsset(code, pattern) {
  const match = code.match(pattern);
  return match?.[1] ?? match?.[0] ?? null;
}

function stripQuery(file) {
  return file.replace(/\?.*$/, "");
}

async function main() {
  const remoteEntry = await fetchText(`${prefix}/remoteEntry.js?${cacheBust}`);
  const exposeRaw = extractAsset(remoteEntry, /(__federation_expose_[^"?]+\.js)/);
  if (!exposeRaw) {
    throw new Error("remoteEntry sem __federation_expose_App");
  }
  const expose = stripQuery(exposeRaw);

  const exposeCode = await fetchText(assetUrl(expose));
  const fnImport = stripQuery(extractAsset(exposeCode, /(__federation_fn_import-[^"?]+\.js)/));
  const appChunk = stripQuery(extractAsset(exposeCode, /(App-[^"?]+\.js)/));

  if (!fnImport || !appChunk) {
    throw new Error(`expose ${expose} sem fn_import ou App chunk`);
  }

  const fnCode = await fetchText(assetUrl(fnImport));
  const appCode = await fetchText(assetUrl(appChunk));

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

  if (exposeCode.includes(`?v=${DELPI_MF_PATCH_VERSION}`)) {
    console.log(`OK  ${expose}: imports com ?v=${DELPI_MF_PATCH_VERSION}`);
  } else {
    console.warn(`WARN ${expose}: imports sem ?v=${DELPI_MF_PATCH_VERSION} — rebuild MFE necessário`);
  }

  if (failed) {
    console.error("\nOrigem sem patch ou build antigo.");
    console.error("Rebuild: ./infra/scripts/up-prod-sequential.sh --no-cache --fase mfe --build", appId);
    console.error("Se o build passou verify Docker: purge Cloudflare → /apps/" + appId + "/assets/*");
    process.exit(1);
  }

  console.log("\nOK: patches MF ativos na origem para", appId);
  console.log("Após deploy com ?v=: purge CF uma vez se browsers ainda falharem.");
}

main().catch((err) => {
  console.error("ERRO:", err.message);
  process.exit(1);
});
