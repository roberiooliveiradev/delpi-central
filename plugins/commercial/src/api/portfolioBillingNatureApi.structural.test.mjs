#!/usr/bin/env node
/**
 * Contratos de natureza gross|net nas APIs da Minha Carteira.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("portfolio billing nature API wiring", () => {
  it("enrichment e billing-series aceitam nature no body", () => {
    const portfolio = readFileSync(join(here, "commercialPortfolioApi.ts"), "utf8");
    const series = readFileSync(join(here, "customerBillingSeriesApi.ts"), "utf8");
    const enrichment = readFileSync(join(here, "customerEnrichmentApi.ts"), "utf8");
    assert.match(portfolio, /nature\?: "gross" \| "net"/);
    assert.match(portfolio, /body\.nature = options\.nature/);
    assert.match(series, /nature\?: "gross" \| "net"/);
    assert.match(series, /\.\.\.\(options\?\.nature \? \{ nature: options\.nature \} : \{\}\)/);
    assert.match(enrichment, /nature\?: "gross" \| "net"/);
  });

  it("analytics share/ranking propagam nature na query", () => {
    const analytics = readFileSync(join(here, "analyticsApi.ts"), "utf8");
    assert.match(
      analytics,
      /if \(params\.nature === "gross" \|\| params\.nature === "net"\)/,
    );
    assert.match(analytics, /searchParams\.set\("nature", params\.nature\)/);
  });
});
