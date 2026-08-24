#!/usr/bin/env node
/**
 * Uso: node plugins/vite/cacheBustEntryPlugin.test.mjs
 */
import assert from "node:assert/strict";

import { cacheBustEntryPlugin, publicHubCacheBustEntryPlugin } from "./cacheBustEntryPlugin.ts";

function test(name, fn) {
  try {
    fn();
    console.log(`ok — ${name}`);
  } catch (error) {
    console.error(`fail — ${name}`);
    throw error;
  }
}

const sampleHtml =
  '<html><body><script type="module" crossorigin src="/p/assets/index-abc123.js"></script></body></html>';

test("publicHubCacheBustEntryPlugin substitui script por import com recuperação", () => {
  const plugin = publicHubCacheBustEntryPlugin();
  const handler = plugin.transformIndexHtml?.handler;
  assert.ok(handler);
  const out = handler(sampleHtml);
  assert.ok(!out.includes('<script type="module" crossorigin src="/p/assets/index-abc123.js">'));
  assert.match(out, /import\(\/\* @vite-ignore \*\/__entry\)/);
  assert.match(out, /delpi-public-hub-asset-recover/);
  assert.match(out, /cache:"reload"/);
  assert.match(out, /const __fail=function/);
  assert.match(out, /fetch\(location\.href,\{cache:"reload"\}/);
});

test("cacheBustEntryPlugin com prefixo /assets/ para portal", () => {
  const plugin = cacheBustEntryPlugin({
    assetPathPrefix: "/assets/",
    sessionKey: "delpi-portal-asset-recover",
  });
  const html =
    '<script type="module" crossorigin src="/assets/index-xyz.js"></script>';
  const out = plugin.transformIndexHtml.handler(html);
  assert.match(out, /delpi-portal-asset-recover/);
});

console.log("cacheBustEntryPlugin: all tests passed");
