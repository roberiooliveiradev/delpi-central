#!/usr/bin/env node
/**
 * PageHero compact — densidade no kit + children legítimos no hero.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "..");
const repoRoot = join(here, "../../..");

function readSrc(...parts) {
  return readFileSync(join(srcRoot, ...parts), "utf8");
}

describe("PageHero composition — density compact (conteúdo no hero)", () => {
  it("CommercialPageHero defaulta density=compact", () => {
    const ui = readSrc("app/commercialUi.ts");
    assert.match(ui, /density:\s*"compact"/);
    assert.match(ui, /CommercialPageHeroBase/);
  });

  it("kit compact densifica padding/gap sem reduzir tipografia base", () => {
    const css = readFileSync(
      join(repoRoot, "plugin-ui/src/styles/page-hero.css"),
      "utf8",
    );
    assert.match(css, /\.delpi-ui-page-hero--compact\s*\{[^}]*padding:\s*12px/s);
    assert.match(css, /\.delpi-ui-page-hero--compact \.delpi-ui-page-hero__content\s*\{[^}]*gap:\s*6px/s);
    assert.match(css, /\.delpi-ui-page-hero--compact \.delpi-ui-page-hero__highlight\s*\{[^}]*padding:\s*10px/s);
    assert.match(css, /\.delpi-ui-page-hero__title\s*\{[^}]*font-size:\s*clamp\(1\.75rem/s);
    assert.doesNotMatch(
      css,
      /\.delpi-ui-page-hero--compact \.delpi-ui-page-hero__title\s*\{[^}]*font-size:/s,
    );
    assert.doesNotMatch(
      css,
      /\.delpi-ui-page-hero--compact \.delpi-ui-page-hero__highlight-label\s*\{[^}]*font-size:/s,
    );
    assert.match(css, /\.delpi-ui-page-hero--compact \.delpi-ui-filter-bar/);
  });

  it("P0 listas mantêm filtros/chips/highlights como children do hero", () => {
    const cases = [
      ["features/overview/OverviewPage.tsx", /AnalyticsFilters/, "Overview"],
      ["pages/OpenOrdersPageImpl.tsx", /FilterBar/, "Open Orders"],
      ["features/customers/pages/CustomersPage.tsx", /CommercialScopeChipBar/, "Customers"],
      ["features/seller-portfolios/SellerPortfoliosPage.tsx", /highlights=\{/, "Seller Portfolios"],
      ["features/analytics/AnalyticsOtdPage.tsx", /AnalyticsFilters/, "Analytics OTD"],
    ];
    for (const [rel, childPattern, label] of cases) {
      const source = readSrc(rel);
      assert.match(source, /<CommercialPageHero\b/, `${label}: PageHero`);
      assert.match(source, /<\/CommercialPageHero>/, `${label}: children no hero`);
      assert.match(source, childPattern, `${label}: conteúdo restaurado`);
    }
  });

  it("MFE não estiliza .delpi-ui-page-hero", () => {
    const css = readSrc("index.css");
    assert.doesNotMatch(css, /\.delpi-ui-page-hero/);
  });
});
