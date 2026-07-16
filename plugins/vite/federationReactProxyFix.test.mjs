#!/usr/bin/env node
/**
 * Testes unitários dos patches MF (sem vite build).
 * Uso: node plugins/vite/federationReactProxyFix.test.mjs
 */
import assert from "node:assert/strict";
import {
  patchBundledReactCjsBridge,
  patchBundledReactConsumerChunk,
  patchFederationFlattenModule,
  patchFederationImportPublishReact,
  patchMfRuntimeImportCacheBust,
  patchRemoteEntryCacheBust,
  publishDelpiMfReact,
  isUsableReact,
  listBundledReactBridgeImports,
  resolveBundledReactBridgeName,
  upgradeUnconditionalReactGlobalPublish,
  DELPI_MF_REACT_GLOBAL,
} from "./federationReactProxyFix.ts";
import { DELPI_MF_PATCH_VERSION } from "./federationPatchVersion.mjs";
import { performance } from "node:perf_hooks";

const REACT_INTERNALS = "__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE";

function portalReact() {
  return {
    useRef: () => "portal",
    [REACT_INTERNALS]: { H: {} },
  };
}

function brokenReact() {
  return {
    useRef: () => "broken",
    [REACT_INTERNALS]: { H: null },
  };
}

const UNPATCHED_H = String.raw`function H(e,t){return typeof e.default=="function"?(Object.keys(e).forEach(s=>{s!=="default"&&(e.default[s]=e[s])}),w[t]=e.default,e.default):(e.default&&(e=Object.assign({},e.default,e)),w[t]=e,e)}`;

const BROKEN_PROXY_H = String.raw`function H(e,t){return typeof e.default=="function"?(Object.keys(e).forEach(s=>{s!=="default"&&(e.default[s]=e[s])}),w[t]=e.default,e.default):(e.default&&(e=(o=e,m=e.default,new Proxy(m,{get(p,r){return r!=="default"&&r in o?o[r]:p[r]},has(p,r){return r in o||r in p},ownKeys(p){const r=new Set([...Reflect.ownKeys(p),...Reflect.ownKeys(o)]);return r.delete("default"),[...r]}}))),w[t]=e,e)}`;

const REACT_SHIM = String.raw`var A={exports:{}},n={};function J(){n.useRef=function(t){return f.H.useRef(t)},n.version="19.2.6",n}var Y;function V(){return Y||(Y=1,A.exports=J()),A.exports}export{V as r};`;

function testFlattenFromObjectAssign() {
  const out = patchFederationImportPublishReact(patchFederationFlattenModule(UNPATCHED_H));
  assert.ok(!out.includes("Object.assign({},e.default,e)"), "Object.assign removido");
  assert.ok(out.includes("var _delpiMod"), "declara _delpiMod");
  assert.ok(!out.includes("e=(o=e"), "não reatribui e");
  assert.ok(out.includes(DELPI_MF_REACT_GLOBAL), "publica react global");
  assert.ok(out.includes("!globalThis.__DELPI_MF_REACT__"), "guard no publish");
}

function testFlattenFromBrokenProxy() {
  const out = patchFederationImportPublishReact(patchFederationFlattenModule(BROKEN_PROXY_H));
  assert.ok(!out.includes("e=(o=e"), "proxy quebrado removido");
  assert.ok(out.includes("_delpiMod=e.default?new Proxy"), "usa _delpiMod");
}

function testFlattenRuntimeStrict() {
  const code = patchFederationImportPublishReact(patchFederationFlattenModule(UNPATCHED_H));
  const result = new Function(
    `const w={}; const mock={useRef:()=>"ok",__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE:{H:{}}}; ${code}; return H({ default: mock }, "react");`,
  )();
  assert.equal(typeof result.useRef, "function");
  assert.ok(isUsableReact(globalThis[DELPI_MF_REACT_GLOBAL]));
  delete globalThis[DELPI_MF_REACT_GLOBAL];
}

function testReactShimUsesGlobal() {
  const out = patchBundledReactCjsBridge(REACT_SHIM);
  assert.ok(out.includes(DELPI_MF_REACT_GLOBAL), "shim consulta global");
  assert.ok(out.includes(REACT_INTERNALS), "shim valida dispatcher H");
}

function testPublishDoesNotOverwritePortalReact() {
  globalThis[DELPI_MF_REACT_GLOBAL] = portalReact();
  publishDelpiMfReact(brokenReact());
  assert.equal(globalThis[DELPI_MF_REACT_GLOBAL].useRef(), "portal");
  delete globalThis[DELPI_MF_REACT_GLOBAL];
}

function testBrokenReactNotUsable() {
  assert.ok(!isUsableReact(brokenReact()));
  assert.ok(isUsableReact(portalReact()));
}

function testAppChunkReactBridgeFallback() {
  const raw = String.raw`import{r as Nu}from"./index-ABC.js";function x(){if(Ws)return al;Ws=1;var e=Nu(),t=DA();return e.useRef}`;
  const out = patchBundledReactConsumerChunk(raw);
  assert.ok(out.includes(REACT_INTERNALS), "App shim valida dispatcher H");
  assert.ok(!out.includes("var e=Nu()"), "init shim não chama Nu() direto");
}

/** Regressão: `$h`=React e `kh`=react-dom — não redirecionar `kh()` para o global React. */
function testAppChunkPrefersDollarReactBridgeOverReactDom() {
  const raw = String.raw`import{r as $h}from"./index-B4SFKWmm.js?v=4";import{r as kh}from"./index-q540vByz.js?v=4";function ld(){var q=$h(),p=kh();var z=q.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,T=p.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;return T.d}`;
  assert.equal(resolveBundledReactBridgeName(raw), "$h", "bridge React é $h");
  const out = patchBundledReactConsumerChunk(raw);
  assert.ok(out.includes("var q=("), "redireciona $h()");
  assert.ok(out.includes("p=kh()"), "não redireciona kh() (react-dom)");
  assert.ok(!out.includes("p=(globalThis.__DELPI_MF_REACT__"), "p não vira React global");
}

/**
 * Regressão api-delpi-console: React core exporta `r`+`g` → `import{r as Lv,g as Xv}`.
 * Regex só `{r as X}` pegava só o bridge react-dom (`Zv`) e redirecionava para o global
 * → `v.__DOM_INTERNALS` undefined → reading 'd'.
 */
function testAppChunkMultiSpecReactImportNotConfusedWithReactDom() {
  const raw = String.raw`import{r as Lv,g as Xv}from"./index-DwdO1xOW.js?v=6";import{r as Zv}from"./index-BxSNP-PZ.js?v=6";function boot(){var o=Lv(),v=Zv();var _=o.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,D=v.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;return D.d}`;
  assert.equal(resolveBundledReactBridgeName(raw), "Lv", "bridge React é Lv (multi-spec)");
  const out = patchBundledReactConsumerChunk(raw);
  assert.ok(out.includes("var o=("), "redireciona Lv()");
  assert.ok(out.includes("v=Zv()"), "não redireciona Zv() (react-dom)");
  assert.ok(!out.includes("v=(globalThis.__DELPI_MF_REACT__"), "v não vira React global");
}

/** Só react-dom no chunk (ou ternário sem assign simples) — não patchar bridge DOM. */
function testAppChunkSkipsLoneReactDomBridge() {
  const raw = String.raw`import{r as Zv}from"./index-BxSNP-PZ.js?v=6";function boot(){var v=((globalThis.__DELPI_MF_REACT__&&typeof globalThis.__DELPI_MF_REACT__.useRef=="function")?globalThis.__DELPI_MF_REACT__:Zv());var D=v.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;return D.d}`;
  assert.equal(resolveBundledReactBridgeName(raw), null, "não escolhe bridge react-dom");
  const out = patchBundledReactConsumerChunk(raw);
  assert.equal(out, raw, "chunk só com react-dom permanece intacto");
}

/**
 * Regressão ReDoS (?v=7): `(?:[^}"']*,)*r as` travava vite build do plugin-ui
 * (milhares de `import{a,b,…}`) em "rendering chunks…".
 */
function testBridgeImportScanIsLinearOnCommaHeavyImports() {
  const specs = Array.from({ length: 800 }, (_, i) => `a${i}`).join(",");
  const bait =
    `import{${specs}}from"./other.js";` +
    "x,".repeat(800) +
    `import{r as Lv,g as Xv}from"./index-ABC.js";var o=Lv();o.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;`;
  const t0 = performance.now();
  assert.deepEqual(listBundledReactBridgeImports(bait), ["Lv"]);
  assert.equal(resolveBundledReactBridgeName(bait), "Lv");
  const ms = performance.now() - t0;
  assert.ok(ms < 200, `scan deve ser linear (<200ms), foi ${ms.toFixed(1)}ms`);
}

/**
 * Regressão dashboard-hr: bridge minificado `rs` — replace ingênuo de `rs()`
 * quebrava `getSelectors()` / `getHours()` → SyntaxError Unexpected token '('.
 */
function testAppChunkShortBridgeDoesNotCorruptIdentifierSuffix() {
  const raw = String.raw`import{r as rs}from"./index-DDrCcACP.js?v=5";function boot(){var e=rs();return e.useRef}function slice(d,getSelectors){return{reducerPath:b,getSelectors:x,api:getSelectors(),hours:d.getHours(),utc:d.getUTCHours()}}`;
  assert.equal(resolveBundledReactBridgeName(raw), "rs");
  const out = patchBundledReactConsumerChunk(raw);
  assert.ok(out.includes("var e=("), "redireciona chamada rs() isolada");
  assert.ok(out.includes("api:getSelectors()"), "preserva getSelectors()");
  assert.ok(!out.includes("get selecto(("), "não corrompe getSelectors()");
  assert.ok(out.includes("d.getHours()"), "preserva getHours()");
  assert.ok(out.includes("d.getUTCHours()"), "preserva getUTCHours()");
  const twice = patchBundledReactConsumerChunk(out);
  assert.equal(twice, out, "patch é idempotente");
}

function testUpgradeUnconditionalPublish() {
  const raw = String.raw`t==="react"&&(globalThis.__DELPI_MF_REACT__=w[t])`;
  const out = upgradeUnconditionalReactGlobalPublish(raw);
  assert.ok(out.includes("!globalThis.__DELPI_MF_REACT__"), "upgrade adiciona guard");
  assert.ok(out.includes("globalThis.__DELPI_MF_REACT__=w[t]"), "upgrade mantém globalThis");
}

function testMfImportCacheBust() {
  const raw = String.raw`import{importShared as _}from"./__federation_fn_import-X.js";import("./App-Y.js")`;
  const out = patchMfRuntimeImportCacheBust(raw);
  assert.ok(out.includes(`__federation_fn_import-X.js?v=${DELPI_MF_PATCH_VERSION}"`), "static import bust");
  assert.ok(out.includes(`import("./App-Y.js?v=${DELPI_MF_PATCH_VERSION}")`), "dynamic import bust");
}

function testRemoteEntryCacheBust() {
  const raw = String.raw`y("/apps/foo/assets/__federation_expose_App-ABC.js")`;
  const out = patchRemoteEntryCacheBust(raw);
  assert.ok(out.includes(`__federation_expose_App-ABC.js?v=${DELPI_MF_PATCH_VERSION}`), "remoteEntry bust");
}

testFlattenFromObjectAssign();
testFlattenFromBrokenProxy();
testFlattenRuntimeStrict();
testReactShimUsesGlobal();
testPublishDoesNotOverwritePortalReact();
testBrokenReactNotUsable();
testUpgradeUnconditionalPublish();
testAppChunkReactBridgeFallback();
testAppChunkPrefersDollarReactBridgeOverReactDom();
testAppChunkMultiSpecReactImportNotConfusedWithReactDom();
testAppChunkSkipsLoneReactDomBridge();
testBridgeImportScanIsLinearOnCommaHeavyImports();
testAppChunkShortBridgeDoesNotCorruptIdentifierSuffix();
testMfImportCacheBust();
testRemoteEntryCacheBust();

console.log("OK: federationReactProxyFix — 15 testes passaram");
