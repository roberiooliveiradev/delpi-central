#!/usr/bin/env node
/**
 * C17 — clique tabela→detalhe: sem interactive órfão; identidade com link.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("C17 table row → detail", () => {
  it("CustomersTable: sem interactive órfão; link + onRowClick", () => {
    const source = readFileSync(
      join(src, "features/customers/components/CustomersTable.tsx"),
      "utf8",
    );
    assert.doesNotMatch(source, /interactive:\s*true/);
    assert.match(source, /onRowClick=\{openCustomer\}/);
    assert.match(source, /cm-link-button/);
    assert.match(source, /CM_HELP\.customers\./);
  });

  it("OpenOrders: interactive só em Cliente e previsão OP", () => {
    const source = readFileSync(join(src, "components/OpenOrdersTable.tsx"), "utf8");
    assert.match(source, /interactive:\s*\n\s*column\.key === "nome_cliente"/);
    assert.doesNotMatch(source, /column\.key === "status"/);
    assert.doesNotMatch(source, /column\.key === "cobertura"/);
    assert.match(source, /onRowClick=\{/);
  });

  it("listas OV/OTD/Propostas têm onRowClick", () => {
    for (const [file, needle] of [
      ["features/analytics/components/CommercialProposalsTable.tsx", /onRowClick=/],
      ["features/analytics/AnalyticsOtdPage.tsx", /onRowClick=\{/],
      ["features/proposals/ProposalsPage.tsx", /onRowClick=\{/],
    ]) {
      assert.match(readFileSync(join(src, file), "utf8"), needle, file);
    }
  });
});
