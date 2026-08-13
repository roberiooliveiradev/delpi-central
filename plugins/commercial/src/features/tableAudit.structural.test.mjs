#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("Table audit P0 (E7.S1)", () => {
  it("superfícies do refino usam padrão kit / sem expand pedidos", () => {
    const orders = readFileSync(
      join(src, "features/customers/components/CustomerOrdersTable.tsx"),
      "utf8",
    );
    assert.match(orders, /CommercialHostDialog/);
    assert.doesNotMatch(orders, /setExpanded|expandedOrder|expandInline/);

    const invoices = readFileSync(
      join(src, "features/customers/billing/components/CustomerInvoicesTable.tsx"),
      "utf8",
    );
    assert.match(invoices, /CommercialHostDialog/);
    assert.match(invoices, /CommercialDataTable/);

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
  });
});
