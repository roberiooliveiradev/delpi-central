#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY,
  OPPORTUNITY_LIST_COLUMNS_STORAGE_KEY,
  OPPORTUNITY_LIST_COLUMN_CATALOG,
  OPPORTUNITY_LIST_FONT_STORAGE_KEY,
  resolveOpportunityListColumnCatalog,
} from "./opportunityTableColumns.ts";

describe("opportunityTableColumns", () => {
  it("expõe storage keys estáveis", () => {
    assert.equal(
      OPPORTUNITY_LIST_COLUMNS_STORAGE_KEY,
      "commercial:analytics-opportunities:table-columns:v1",
    );
    assert.equal(
      OPPORTUNITY_LIST_FONT_STORAGE_KEY,
      "commercial:analytics-opportunities:table-font-size:v1",
    );
    assert.match(OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY, /collaborator/);
  });

  it("catálogo global inclui vendedor e proposta", () => {
    const keys = OPPORTUNITY_LIST_COLUMN_CATALOG.map((c) => c.key);
    assert.ok(keys.includes("seller"));
    assert.ok(keys.includes("proposal-doc"));
    assert.ok(keys.includes("customer"));
  });

  it("resolveOpportunityListColumnCatalog respeita hide/show", () => {
    const conta = resolveOpportunityListColumnCatalog({
      hideCustomerColumn: true,
      hideSellerColumn: true,
      showOpenProposal: true,
    });
    const keys = conta.map((c) => c.key);
    assert.ok(!keys.includes("customer"));
    assert.ok(!keys.includes("seller"));
    assert.ok(keys.includes("proposal-doc"));
    assert.ok(keys.includes("ov"));

    const noProposal = resolveOpportunityListColumnCatalog({
      showOpenProposal: false,
    });
    assert.ok(!noProposal.some((c) => c.key === "proposal-doc"));
  });
});
