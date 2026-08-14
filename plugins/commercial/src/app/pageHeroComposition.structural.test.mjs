#!/usr/bin/env node
/**
 * E3.S7 — PageHero compact: faixa de título sem filtros/children nos P0.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "..");

function readSrc(...parts) {
  return readFileSync(join(srcRoot, ...parts), "utf8");
}

/** Hero sem children JSX (self-closing ou sem tag de fechamento). */
function assertHeroTitleStripOnly(source, label) {
  assert.doesNotMatch(
    source,
    /<\/CommercialPageHero>/,
    `${label}: filtros/children não devem ficar dentro do PageHero`,
  );
  assert.match(source, /<CommercialPageHero\b/, `${label}: usa CommercialPageHero`);
}

describe("PageHero composition — density compact + filtros fora", () => {
  it("CommercialPageHero defaulta density=compact", () => {
    const ui = readSrc("app/commercialUi.ts");
    assert.match(ui, /density:\s*"compact"/);
    assert.match(ui, /CommercialPageHeroBase/);
    assert.match(ui, /createDashboardMetricStrip/);
  });

  it("P0 listas: hero só faixa de título + cm-page-filters", () => {
    const pages = [
      ["features/overview/OverviewPage.tsx", "Overview"],
      ["pages/OpenOrdersPageImpl.tsx", "Open Orders"],
      ["features/customers/pages/CustomersPage.tsx", "Customers"],
      ["features/seller-portfolios/SellerPortfoliosPage.tsx", "Seller Portfolios"],
      ["features/analytics/AnalyticsOtdPage.tsx", "Analytics OTD"],
      ["features/analytics/AnalyticsOpportunitiesPage.tsx", "Analytics Opportunities"],
    ];
    for (const [rel, label] of pages) {
      const source = readSrc(rel);
      assertHeroTitleStripOnly(source, label);
      assert.match(source, /cm-page-filters/, `${label}: filtros em cm-page-filters`);
    }
  });

  it("Seller Portfolios: MetricStrip fora do hero e sem CTA duplicada na lista", () => {
    const page = readSrc("features/seller-portfolios/SellerPortfoliosPage.tsx");
    const list = readSrc("features/seller-portfolios/SellerPortfoliosList.tsx");
    assert.match(page, /CommercialMetricStrip/);
    assert.doesNotMatch(page, /highlights=\{/);
    assert.doesNotMatch(list, /Nova carteira/);
    assert.doesNotMatch(list, /headerActions/);
  });

  it("Admin hub: hero self-closing (filtros já fora)", () => {
    for (const rel of [
      "features/administration/AdministrationHomePage.tsx",
      "features/administration/AdministrationTeamPage.tsx",
      "features/administration/AdministrationGroupsPage.tsx",
    ]) {
      assertHeroTitleStripOnly(readSrc(rel), rel);
    }
  });

  it("MFE não estiliza .delpi-ui-page-hero", () => {
    const css = readSrc("index.css");
    assert.doesNotMatch(css, /\.delpi-ui-page-hero/);
  });
});
