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
  upgradeUnconditionalReactGlobalPublish,
  DELPI_MF_REACT_GLOBAL,
} from "./federationReactProxyFix.ts";

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

function testUpgradeUnconditionalPublish() {
  const raw = String.raw`t==="react"&&(globalThis.__DELPI_MF_REACT__=w[t])`;
  const out = upgradeUnconditionalReactGlobalPublish(raw);
  assert.ok(out.includes("!globalThis.__DELPI_MF_REACT__"), "upgrade adiciona guard");
  assert.ok(out.includes("globalThis.__DELPI_MF_REACT__=w[t]"), "upgrade mantém globalThis");
}

function testMfImportCacheBust() {
  const raw = String.raw`import{importShared as _}from"./__federation_fn_import-X.js";import("./App-Y.js")`;
  const out = patchMfRuntimeImportCacheBust(raw);
  assert.ok(out.includes('__federation_fn_import-X.js?v=4"'), "static import bust");
  assert.ok(out.includes('import("./App-Y.js?v=4")'), "dynamic import bust");
}

function testRemoteEntryCacheBust() {
  const raw = String.raw`y("/apps/foo/assets/__federation_expose_App-ABC.js")`;
  const out = patchRemoteEntryCacheBust(raw);
  assert.ok(out.includes("__federation_expose_App-ABC.js?v=4"), "remoteEntry bust");
}

testFlattenFromObjectAssign();
testFlattenFromBrokenProxy();
testFlattenRuntimeStrict();
testReactShimUsesGlobal();
testPublishDoesNotOverwritePortalReact();
testBrokenReactNotUsable();
testUpgradeUnconditionalPublish();
testAppChunkReactBridgeFallback();
testMfImportCacheBust();
testRemoteEntryCacheBust();

console.log("OK: federationReactProxyFix — 10 testes passaram");
