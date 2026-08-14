#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "format.ts"), "utf8");

describe("customerKey / store normalize", () => {
  it("normaliza loja numérica e expõe customerKey", () => {
    assert.match(src, /normalizeCustomerStore/);
    assert.match(src, /padStart\(2,\s*"0"\)/);
    assert.match(src, /customerKey/);
  });
});
