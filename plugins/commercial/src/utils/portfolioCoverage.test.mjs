#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  overlappingCustomerKeySetForPortfolio,
  overlappingPortfolioIdSet,
  otherPortfolioNamesForCustomer,
  readCoverageLinkWarning,
  stripPortfolioCoverageFields,
} from "./portfolioCoverage.ts";

const AUDIT = {
  overlapping_count: 1,
  overlapping: [
    {
      customer_code: "100",
      customer_store: "01",
      customer_name: "Cliente",
      portfolio_ids: ["p1", "p2"],
      portfolios: [
        { id: "p1", display_name: "Carteira A" },
        { id: "p2", display_name: "Carteira B" },
      ],
    },
  ],
  portfolios_with_overlap: [
    { id: "p1", display_name: "Carteira A", overlapping_customer_count: 1 },
    { id: "p2", display_name: "Carteira B", overlapping_customer_count: 1 },
  ],
  gap: { available: false, reason: "customer_universe_not_available" },
};

describe("portfolioCoverage helpers", () => {
  it("extrai ids e chaves de overlapping do audit", () => {
    assert.deepEqual([...overlappingPortfolioIdSet(AUDIT)].sort(), ["p1", "p2"]);
    assert.deepEqual(
      [...overlappingCustomerKeySetForPortfolio(AUDIT, "p1")],
      ["100|01"],
    );
    assert.deepEqual(otherPortfolioNamesForCustomer(AUDIT, "p1", "100", "01"), [
      "Carteira B",
    ]);
  });

  it("remove campos de warning do payload de add-customer", () => {
    const result = stripPortfolioCoverageFields({
      id: "p1",
      user_id: "u1",
      display_name: "A",
      active: true,
      customer_count: 1,
      customers: [],
      warnings: [
        {
          code: "customer_in_other_portfolios",
          message: "aviso",
          other_portfolios: [{ id: "p2", display_name: "B" }],
        },
      ],
      coverage_warning: {
        code: "customer_in_other_portfolios",
        message: "aviso",
        other_portfolios: [{ id: "p2", display_name: "B" }],
      },
    });
    assert.equal(result.id, "p1");
    assert.equal("warnings" in result, false);
    assert.equal("coverage_warning" in result, false);
    assert.equal(
      readCoverageLinkWarning({
        ...result,
        coverage_warning: {
          code: "customer_in_other_portfolios",
          message: "aviso",
          other_portfolios: [],
        },
      })?.code,
      "customer_in_other_portfolios",
    );
  });
});
