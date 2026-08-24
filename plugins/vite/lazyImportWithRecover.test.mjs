#!/usr/bin/env node
/**
 * Uso: node plugins/vite/lazyImportWithRecover.test.mjs
 */
import assert from "node:assert/strict";

import {
  DELPI_PUBLIC_HUB_RECOVER_KEY,
  requestAssetRecover,
} from "./assetRecover.ts";
import { lazyImportWithRecover } from "./lazyImportWithRecover.ts";

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

const storage = new Map();
globalThis.sessionStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
};

await test("repassa o módulo quando o import funciona", async () => {
  storage.clear();
  const mod = { default: "ok" };
  const load = lazyImportWithRecover(() => Promise.resolve(mod));
  assert.equal(await load(), mod);
});

await test("repassa erros que não são chunk stale", async () => {
  storage.clear();
  const load = lazyImportWithRecover(() => Promise.reject(new Error("syntax error")));
  await assert.rejects(() => load(), /syntax error/);
  assert.equal(storage.get(DELPI_PUBLIC_HUB_RECOVER_KEY), undefined);
});

await test("redireciona uma vez em falha de chunk dinâmico", async () => {
  storage.clear();
  const replaceCalls = [];
  mockLocation("https://minhadelpi.com.br/p/tv-dashboard/present/abc", (url) => {
    replaceCalls.push(url);
  });

  const load = lazyImportWithRecover(() =>
    Promise.reject(new Error("Failed to fetch dynamically imported module: /p/assets/foo.js")),
  );

  const pending = load();
  await Promise.race([pending, new Promise((resolve) => setTimeout(resolve, 0))]);
  assert.equal(replaceCalls.length, 1);
  assert.match(replaceCalls[0], /_recover=/);
  assert.equal(storage.get(DELPI_PUBLIC_HUB_RECOVER_KEY), "1");
});

await test("não redireciona de novo na mesma sessão", async () => {
  storage.clear();
  storage.set(DELPI_PUBLIC_HUB_RECOVER_KEY, "1");
  const replaceCalls = [];
  mockLocation("https://minhadelpi.com.br/p/tv-dashboard/present/abc", (url) => {
    replaceCalls.push(url);
  });

  const load = lazyImportWithRecover(() =>
    Promise.reject(new Error("Failed to fetch dynamically imported module")),
  );

  await assert.rejects(() => load(), /Failed to fetch dynamically imported module/);
  assert.equal(replaceCalls.length, 0);
});

console.log("lazyImportWithRecover: all tests passed");
