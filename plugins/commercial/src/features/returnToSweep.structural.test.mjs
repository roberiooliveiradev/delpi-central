#!/usr/bin/env node
/**
 * E7.S3 — Sweep returnTo / sem expand legado nas superfícies do refino Conta/Propostas.
 */
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

describe("returnTo sweep (E7.S3)", () => {
  it("detalhes do escopo usam resolvePagePathBack + CommercialPagePath", () => {
    const details = [
      "features/customers/pages/CustomerOrderDetailPage.tsx",
      "features/open-orders/OpenOrderLineDetailPage.tsx",
      "features/open-orders/OpenOrderOpDetailPage.tsx",
      "features/analytics/AnalyticsOpportunityDetailPage.tsx",
      "features/proposals/ProposalDetailPage.tsx",
    ];
    for (const rel of details) {
      const text = read(rel);
      assert.match(text, /resolvePagePathBack/, `${rel} sem resolvePagePathBack`);
      assert.match(text, /CommercialPagePath/, `${rel} sem CommercialPagePath`);
    }
  });

  it("listas propagam returnTo canônico ao abrir detalhe", () => {
    assert.match(read("features/customers/components/CustomerOrdersTable.tsx"), /currentLocationAsReturnTo/);
    assert.match(read("features/proposals/ProposalsDocumentsTable.tsx"), /currentLocationAsReturnTo/);
    assert.match(
      read("features/analytics/components/OpenProposalFromOpportunityButton.tsx"),
      /currentLocationAsReturnTo/,
    );
  });

  it("Conta pedidos usa expand canônico do kit + row click", () => {
    const orders = read("features/customers/components/CustomerOrdersTable.tsx");
    assert.match(orders, /renderExpandedRow/);
    assert.match(orders, /expandedRowKey/);
    assert.match(orders, /onRowClick=\{openOrderDetail\}/);
    assert.doesNotMatch(orders, /CommercialHostDialog/);
    assert.doesNotMatch(orders, /expandedOrder|expandInline/);
  });
});
