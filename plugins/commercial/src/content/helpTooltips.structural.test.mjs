#!/usr/bin/env node
/**
 * C16 — matriz mínima de CM_HELP + páginas migradas consomem CM_HELP.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");
const helpSource = readFileSync(join(src, "content/helpTooltips.ts"), "utf8");

function assertHelpKey(dottedKey) {
  const parts = dottedKey.split(".");
  assert.equal(parts.length, 2, `chave deve ser section.key: ${dottedKey}`);
  const [section, key] = parts;
  const sectionRe = new RegExp(`\\b${section}\\s*:\\s*\\{`);
  assert.match(helpSource, sectionRe, `seção ${section}`);
  const keyRe = new RegExp(`\\b${key}\\s*:`);
  const sectionStart = helpSource.search(sectionRe);
  assert.ok(sectionStart >= 0, section);
  const after = helpSource.slice(sectionStart);
  const nextSection = after.search(/\n  [a-zA-Z][a-zA-Z0-9]*:\s*\{/);
  const block =
    nextSection > 0 ? after.slice(0, nextSection) : after.slice(0, after.indexOf("\n} as const"));
  assert.match(block, keyRe, `faltando ${dottedKey}`);
  assert.match(block, new RegExp(`${key}\\s*:\\s*"[^"]{12,}"`), `${dottedKey} string curta`);
}

describe("CM_HELP matriz (C16)", () => {
  it("exporta chaves obrigatórias da matriz por superfície", () => {
    const required = [
      "shell.portal",
      "shell.scope",
      "shell.navHome",
      "shell.navOverview",
      "shell.navMyTasks",
      "shell.navOrders",
      "shell.navCustomers",
      "shell.navAdmin",
      "interactionRooms.panel",
      "home.overview",
      "home.alerts",
      "home.shortcuts",
      "overview.page",
      "overview.filters",
      "overview.kpis",
      "overview.rolSeries",
      "overview.rolSeriesYoy",
      "overview.closingRateSeries",
      "overview.closingRateSeriesYoy",
      "overview.funnel",
      "overview.closingRate",
      "overview.openPortfolio",
      "overview.billingNatureNet",
      "overview.billingNatureOpenOrder",
      "analytics.portfolioFilter",
      "analytics.filters",
      "analytics.otdPage",
      "analytics.otdLines",
      "analytics.opportunitiesPage",
      "analytics.searchOpportunities",
      "analytics.opportunityStatus",
      "analytics.tableRowOpensDetail",
      "openOrders.page",
      "openOrders.tableRowOpensDetail",
      "openOrders.filterLate",
      "openOrders.filterPostponed",
      "myDay.worklist",
      "customers.page",
      "customers.list",
      "customers.tableRowOpensDetail",
      "customerDetail.header",
      "customerDetail.contacts",
      "customerDetail.avatarChange",
      "customerDetail.avatarRemove",
      "customerDetail.opportunities",
      "customerDetail.billingSeriesAccount",
      "customerDetail.billingSeriesTrend",
      "customerDetail.ordersSituationFilter",
      "customerDetail.ordersSearch",
      "customerDetail.opportunitiesStatusFilter",
      "customerDetail.opportunitiesSearch",
      "customerDetail.opportunitiesDateStart",
      "customerDetail.opportunitiesDateEnd",
      "customerDetail.opportunitiesProductCode",
      "customerDetail.opportunitiesProductGroup",
      "customerDetail.tableRowOpensDetail",
      "customers.contacts",
      "users.profile",
      "users.access",
      "users.shortcuts",
      "users.editMode",
      "proposals.page",
      "proposals.list",
      "proposals.scopeNote",
      "proposals.tableRowOpensDetail",
      "administration.panel",
      "administration.portfolios",
      "administration.members",
    ];
    for (const key of required) assertHelpKey(key);
  });

  it("páginas migradas consomem CM_HELP", () => {
    const files = [
      "features/overview/OverviewPage.tsx",
      "features/analytics/AnalyticsOtdPage.tsx",
      "features/analytics/AnalyticsOpportunitiesPage.tsx",
      "features/analytics/components/AnalyticsFilters.tsx",
      "features/customers/components/CustomerOpportunitiesSection.tsx",
      "features/proposals/ProposalsPage.tsx",
      "features/administration/AdministrationHomePage.tsx",
      "app/PluginShell.tsx",
    ];
    for (const file of files) {
      const source = readFileSync(join(src, file), "utf8");
      assert.match(source, /CM_HELP/, file);
    }
  });

  it("Overview expõe metodologia hit rate e carteira≠PCP", () => {
    const source = readFileSync(join(src, "features/overview/OverviewPage.tsx"), "utf8");
    const helps = readFileSync(join(src, "content/helpTooltips.ts"), "utf8");
    assert.match(source, /CM_HELP\.overview\.closingRate/);
    assert.match(source, /CM_HELP\.overview\.funnel/);
    assert.match(source, /CM_HELP\.overview\.openPortfolio/);
    assert.match(source, /CM_HELP\.overview\.closingRateSeries/);
    assert.match(source, /cm-gestao-charts-grid--auto-span/);
    assert.match(source, /AnalyticsClosingRateSeriesChart/);
    assert.match(source, /≠ PCP|Em aberto \(agora\)/);
    assert.match(helps, /openPortfolio:[\s\S]*PCP/);
    assert.match(helps, /openPortfolio:[\s\S]*não deve ser somada ao ROL|não some com ROL/i);
  });
});
