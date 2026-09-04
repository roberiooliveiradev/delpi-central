#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("Table audit P0 (E7.S1)", () => {
  it("superfícies do refino usam padrão kit / expand canônico em pedidos", () => {
    const orders = readFileSync(
      join(src, "features/customers/components/CustomerOrdersTable.tsx"),
      "utf8",
    );
    assert.match(orders, /renderExpandedRow/);
    assert.match(orders, /expandedRowKey/);
    assert.match(orders, /onRowClick/);
    assert.match(orders, /CUSTOMER_ORDERS_CONTENT/);
    assert.doesNotMatch(orders, /CommercialHostDialog/);
    assert.doesNotMatch(orders, /Ver linhas|Abrir pedido/);
    assert.doesNotMatch(orders, /expandedOrder|expandInline/);

    const invoices = readFileSync(
      join(src, "features/customers/billing/components/CustomerInvoicesTable.tsx"),
      "utf8",
    );
    assert.match(invoices, /onRowClick/);
    assert.match(invoices, /navigateCustomerInvoiceDetail/);
    assert.match(invoices, /CommercialDataTable/);
    assert.doesNotMatch(invoices, /CommercialHostDialog/);
    assert.doesNotMatch(invoices, /Ver itens/);

    const proposals = readFileSync(
      join(src, "features/proposals/ProposalsDocumentsTable.tsx"),
      "utf8",
    );
    assert.match(proposals, /CommercialDataListToolbar/);
    assert.match(proposals, /CommercialInteractiveDataCard/);

    const opp = readFileSync(
      join(src, "features/analytics/components/CommercialProposalsTable.tsx"),
      "utf8",
    );
    assert.match(opp, /CommercialStatusBadge/);
    assert.match(opp, /OpenProposalFromOpportunityButton/);
    assert.match(opp, /statusBadgeVariant|status_category/);
    assert.match(opp, /interactive:\s*true/);
    assert.match(opp, /CommercialDataListToolbar/);
    assert.match(opp, /useTableColumnVisibility|useOpportunitiesTablePreferences/);
    assert.doesNotMatch(opp, /sortTableRows\(/);

    const myDay = readFileSync(join(src, "features/my-day/MyDayPage.tsx"), "utf8");
    assert.match(myDay, /CommercialSectionCard/);
    assert.match(myDay, /CommercialEmptyState/);
    assert.doesNotMatch(myDay, /\bSectionCard\b|\bEmptyState\b/);

    const ovDetail = readFileSync(
      join(src, "features/analytics/AnalyticsOpportunityDetailPage.tsx"),
      "utf8",
    );
    assert.match(ovDetail, /CommercialSectionCard/);
    assert.match(ovDetail, /CommercialEmptyState/);
    assert.doesNotMatch(ovDetail, /\bSectionCard\b|\bEmptyState\b/);
  });
});
