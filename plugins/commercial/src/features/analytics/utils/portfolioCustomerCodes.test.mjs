#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  resolvePortfolioCustomerCodes,
  serializeCustomerCodesCsv,
} from "./portfolioCustomerCodes.ts";

describe("portfolioCustomerCodes", () => {
  it("null seller → null codes (consolidado)", () => {
    assert.equal(resolvePortfolioCustomerCodes(null, []), null);
    assert.equal(serializeCustomerCodesCsv(null), undefined);
  });

  it("seller sem carteira → lista vazia", () => {
    assert.deepEqual(resolvePortfolioCustomerCodes("missing", []), []);
    assert.equal(serializeCustomerCodesCsv([]), "");
  });

  it("dedupe códigos da carteira", () => {
    const codes = resolvePortfolioCustomerCodes("s1", [
      {
        id: "s1",
        user_id: "u",
        display_name: "A",
        active: true,
        customer_count: 2,
        customers: [
          { customer_code: "001", customer_store: "01", customer_name: null },
          { customer_code: "001", customer_store: "02", customer_name: null },
          { customer_code: "002", customer_store: "01", customer_name: "X" },
        ],
      },
    ]);
    assert.deepEqual(codes, ["001", "002"]);
    assert.equal(serializeCustomerCodesCsv(codes), "001,002");
  });
});
