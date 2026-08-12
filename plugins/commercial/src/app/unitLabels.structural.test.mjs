#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

function read(rel) {
  return readFileSync(join(src, rel), "utf8");
}

describe("E1.S2 — labels Unidade SC/ES em filtros e tabelas", () => {
  it("FilterBar e colunas usam kit operational unit", () => {
    const filterBar = read("components/FilterBar.tsx");
    assert.match(filterBar, /OPERATIONAL_UNIT_FIELD_LABEL/);
    assert.match(filterBar, /buildOperationalUnitOptions/);
    assert.doesNotMatch(filterBar, /label="Filial"/);

    const columns = read("utils/tableColumns.ts");
    assert.match(columns, /OPERATIONAL_UNIT_COLUMN_LABEL/);
  });

  it("pedidos/carteira/propostas/OTD formatam unidade", () => {
    for (const file of [
      "components/OpenOrdersLineCard.tsx",
      "components/OpenOrdersTable.tsx",
      "utils/exportOpenOrdersExcel.ts",
      "features/open-orders/OpenOrderLineDetailPage.tsx",
      "features/customers/components/CustomerOrdersTable.tsx",
      "features/customers/components/CustomerAttentionOrders.tsx",
      "features/customers/billing/components/CustomerInvoicesTable.tsx",
      "features/proposals/ProposalDetailPage.tsx",
      "features/analytics/AnalyticsOtdLineDetailPage.tsx",
      "features/analytics/AnalyticsOpportunityDetailPage.tsx",
      "features/analytics/AnalyticsOtdPage.tsx",
    ]) {
      const source = read(file);
      assert.match(source, /formatOperationalUnitCode|ANALYTICS_OTD_SERIES_LABELS/, file);
      assert.doesNotMatch(source, /Filial \$\{|label: "Filial"|header: "Filial"|OTD SC|OTD ES/, file);
    }
  });
});
