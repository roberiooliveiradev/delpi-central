#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "CustomerOpportunitiesSection.tsx"), "utf8");

describe("CustomerOpportunitiesSection filter UX", () => {
  it("mantém FilterBar fora do gate de loading inicial", () => {
    assert.match(source, /CommercialFilterBarShell/);
    assert.match(source, /showInitialLoader/);
    assert.doesNotMatch(
      source,
      /\{!loading && !error \? \([\s\S]*CommercialFilterBarShell/,
    );
    const filterIdx = source.indexOf("CommercialFilterBarShell");
    const loaderIdx = source.indexOf("showInitialLoader");
    assert.ok(filterIdx > 0 && loaderIdx > filterIdx);
  });

  it("debounceia filtros de texto antes do fetch", () => {
    assert.match(source, /TEXT_FILTER_DEBOUNCE_MS/);
    assert.match(source, /debouncedSearch/);
    assert.match(source, /debouncedProductCode/);
    assert.match(source, /debouncedProductGroup/);
    assert.match(source, /getCommercialProposals/);
  });
});
