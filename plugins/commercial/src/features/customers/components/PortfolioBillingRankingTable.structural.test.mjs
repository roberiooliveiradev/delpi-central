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
    assert.match(source, /collapsible/);
    assert.match(source, /defaultOpen=\{false\}/);
    assert.doesNotMatch(source, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
    assert.doesNotMatch(source, /\.delpi-ui-/);
  });

  it("CustomersPage monta o ranking após a série de faturamento", () => {
    const page = readFileSync(join(here, "../pages/CustomersPage.tsx"), "utf8");
    assert.match(page, /PortfolioBillingRankingTable/);
    assert.match(page, /CustomerBillingSeriesChart/);
  });
});
