#!/usr/bin/env node
/**
 * Testes unitários dos patches MF (sem vite build).
 * Uso: node plugins/vite/federationReactProxyFix.test.mjs
 */
import assert from "node:assert/strict";
import {
  patchBundledReactCjsBridge,
  patchFederationFlattenModule,
  patchFederationImportPublishReact,
  DELPI_MF_REACT_GLOBAL,
} from "./federationReactProxyFix.ts";

const UNPATCHED_H = String.raw`function H(e,t){return typeof e.default=="function"?(Object.keys(e).forEach(s=>{s!=="default"&&(e.default[s]=e[s])}),w[t]=e.default,e.default):(e.default&&(e=Object.assign({},e.default,e)),w[t]=e,e)}`;

const BROKEN_PROXY_H = String.raw`function H(e,t){return typeof e.default=="function"?(Object.keys(e).forEach(s=>{s!=="default"&&(e.default[s]=e[s])}),w[t]=e.default,e.default):(e.default&&(e=(o=e,m=e.default,new Proxy(m,{get(p,r){return r!=="default"&&r in o?o[r]:p[r]},has(p,r){return r in o||r in p},ownKeys(p){const r=new Set([...Reflect.ownKeys(p),...Reflect.ownKeys(o)]);return r.delete("default"),[...r]}}))),w[t]=e,e)}`;

const REACT_SHIM = String.raw`var A={exports:{}},n={};function J(){n.useRef=function(t){return f.H.useRef(t)},n.version="19.2.6",n}var Y;function V(){return Y||(Y=1,A.exports=J()),A.exports}export{V as r};`;

function testFlattenFromObjectAssign() {
  const out = patchFederationImportPublishReact(patchFederationFlattenModule(UNPATCHED_H));
  assert.ok(!out.includes("Object.assign({},e.default,e)"), "Object.assign removido");
  assert.ok(out.includes("var _delpiMod"), "declara _delpiMod");
  assert.ok(!out.includes("e=(o=e"), "não reatribui e");
  assert.ok(out.includes(DELPI_MF_REACT_GLOBAL), "publica react global");
}

function testFlattenFromBrokenProxy() {
  const out = patchFederationImportPublishReact(patchFederationFlattenModule(BROKEN_PROXY_H));
  assert.ok(!out.includes("e=(o=e"), "proxy quebrado removido");
  assert.ok(out.includes("_delpiMod=e.default?new Proxy"), "usa _delpiMod");
}

function testFlattenRuntimeStrict() {
  const code = patchFederationImportPublishReact(patchFederationFlattenModule(UNPATCHED_H));
  const result = new Function(
    `const w={}; ${code}; return H({ default: { useRef: () => "ok" } }, "react");`,
  )();
  assert.equal(typeof result.useRef, "function");
  assert.equal(globalThis[DELPI_MF_REACT_GLOBAL]?.useRef?.(), "ok");
  delete globalThis[DELPI_MF_REACT_GLOBAL];
}

function testReactShimUsesGlobal() {
  const out = patchBundledReactCjsBridge(REACT_SHIM);
  assert.ok(out.includes(DELPI_MF_REACT_GLOBAL), "shim consulta global");
  assert.match(out, /function V\(\)\{const __g=globalThis\.__DELPI_MF_REACT__;if\(__g\)return __g;return/);
}

testFlattenFromObjectAssign();
testFlattenFromBrokenProxy();
testFlattenRuntimeStrict();
testReactShimUsesGlobal();

console.log("OK: federationReactProxyFix — 4 testes passaram");
