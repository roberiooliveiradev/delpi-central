#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("PortfolioBillingRankingTable", () => {
  it("usa BFF commercial + Excel + DataTable sem api-delpi nem CSS de kit", () => {
    const source = readFileSync(join(here, "PortfolioBillingRankingTable.tsx"), "utf8");
    assert.match(source, /getPortfolioBillingRanking/);
    assert.match(source, /CM_HELP\.customers\.billingRanking/);
    assert.match(source, /CommercialDataTable/);
    assert.match(source, /CommercialExcelExportButton/);
    assert.match(source, /runTabularExport/);
    assert.match(source, /canUseTeamScope/);
    assert.match(source, /group_by/);
    assert.match(source, /active/);
    assert.doesNotMatch(source, /collapsible/);
    assert.doesNotMatch(source, /defaultOpen/);
    assert.match(source, /OtdCustomerIdentityCell/);
    assert.match(source, /useCustomerAvatarPresence/);
    assert.match(source, /CommercialAvatar/);
    assert.match(source, /CommercialCompareSparkline/);
    assert.match(source, /CommercialTrendDelta/);
    assert.match(source, /order/);
    assert.match(source, /limit/);
    assert.match(source, /RANKING_LIMIT_OPTIONS/);
    assert.match(source, /Maiores altas/);
    assert.match(source, /Maiores quedas/);
    assert.match(source, /CommercialSelectField/);
    assert.match(source, /CommercialDataCellValue/);
    assert.match(source, /usePortfolioBillingTablePreferences/);
    assert.match(source, /CommercialTableColumnVisibilityMenu/);
    assert.match(source, /enableColumnReorder/);
    assert.doesNotMatch(source, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
    assert.doesNotMatch(source, /\.delpi-ui-/);
  });

  it("CustomersPage alterna painéis com SegmentToggle e ranking/série", () => {
    const page = readFileSync(join(here, "../pages/CustomersPage.tsx"), "utf8");
    assert.match(page, /PortfolioBillingRankingTable/);
    assert.match(page, /CustomerBillingSeriesChart/);
    assert.match(page, /CommercialSegmentToggle/);
    assert.match(page, /customers-workspace-panel/);
    assert.match(page, /customers-billing-nature/);
    assert.match(page, /setBillingNature/);
    assert.match(page, /setPanel/);
    assert.match(page, /active=\{panel === "billing"\}/);
    assert.match(page, /active=\{panel === "abc"\}/);
    assert.match(page, /active=\{panel === "ranking"\}/);
    assert.match(page, /billingNature=\{billingNature\}/);
  });
});
