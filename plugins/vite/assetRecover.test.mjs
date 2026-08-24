#!/usr/bin/env node
/**
 * Uso: npx tsx plugins/vite/assetRecover.test.mjs
 */
import assert from "node:assert/strict";

import {
  DELPI_PUBLIC_HUB_RECOVER_KEY,
  clearAssetRecoverLock,
  isStaleModuleLoadError,
  requestAssetRecover,
} from "./assetRecover.ts";

const storage = new Map();
globalThis.sessionStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
};

function mockLocation(href, replace) {
  globalThis.location = { href, replace };
}

async function test(name, fn) {
  try {
    await fn();
    console.log(`ok — ${name}`);
  } catch (error) {
    console.error(`fail — ${name}`);
    throw error;
  }
}

await test("isStaleModuleLoadError reconhece falha de import dinâmico", () => {
  assert.equal(
    isStaleModuleLoadError("Failed to fetch dynamically imported module: /p/assets/foo.js"),
    true,
  );
  assert.equal(isStaleModuleLoadError("syntax error"), false);
});

await test("requestAssetRecover redireciona uma vez", async () => {
  storage.clear();
  const replaceCalls = [];
  mockLocation("https://minhadelpi.com.br/p/tv-dashboard/present/abc", (url) => {
    replaceCalls.push(url);
  });
  assert.equal(requestAssetRecover(), true);
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(replaceCalls.length, 1);
  assert.match(replaceCalls[0], /_recover=/);
  assert.equal(storage.get(DELPI_PUBLIC_HUB_RECOVER_KEY), "1");
});

await test("requestAssetRecover com force limpa trava e tenta de novo", async () => {
  storage.set(DELPI_PUBLIC_HUB_RECOVER_KEY, "1");
  const replaceCalls = [];
  mockLocation("https://minhadelpi.com.br/p/tv-dashboard/present/abc", (url) => {
    replaceCalls.push(url);
  });
  assert.equal(requestAssetRecover({ force: true }), true);
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(replaceCalls.length, 1);
});

await test("clearAssetRecoverLock remove a trava", () => {
  storage.set(DELPI_PUBLIC_HUB_RECOVER_KEY, "1");
  clearAssetRecoverLock();
  assert.equal(storage.get(DELPI_PUBLIC_HUB_RECOVER_KEY), undefined);
});

console.log("assetRecover: all tests passed");
