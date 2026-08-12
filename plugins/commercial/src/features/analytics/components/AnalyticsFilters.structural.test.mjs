#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("AnalyticsFilters — carteira multi e unidade", () => {
  it("carteira multi-select com busca e unidade emptyLabel Todas", () => {
    const source = readFileSync(join(here, "AnalyticsFilters.tsx"), "utf8");
    assert.match(source, /multiple/);
    assert.match(source, /SellerScopeFilter/);
    assert.match(source, /emptyLabel=\"Todas\"/);
    assert.match(source, /searchable/);
    assert.doesNotMatch(source, /onSellerId\?/);
  });
});
