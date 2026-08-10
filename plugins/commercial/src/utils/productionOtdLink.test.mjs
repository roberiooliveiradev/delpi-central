#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatOtdDaysDiff,
  linkedPiOrders,
  parseProductionLinkSummary,
} from "./productionOtdLink.ts";

describe("parseProductionLinkSummary", () => {
  it("normaliza contadores", () => {
    assert.deepEqual(
      parseProductionLinkSummary({
        order_number: "106015",
        total_pi_orders: "4",
        on_time_ops: 4,
        late_ops: 0,
        open_ops: 0,
      }),
      {
        order_number: "106015",
        link_field: null,
        total_pi_orders: 4,
        on_time_ops: 4,
        late_ops: 0,
        open_ops: 0,
      },
    );
  });
});

describe("linkedPiOrders", () => {
  it("prioriza product_type PI e limita", () => {
    const rows = linkedPiOrders(
      [
        { production_order: "A", product_type: "PA" },
        { production_order: "B", product_type: "PI" },
        { production_order: "C", product_type: "PI" },
        { production_order: "D", product_type: "PI" },
      ],
      2,
    );
    assert.deepEqual(
      rows.map((r) => r.production_order),
      ["B", "C"],
    );
  });
});

describe("formatOtdDaysDiff", () => {
  it("formata sinal e vazio", () => {
    assert.equal(formatOtdDaysDiff(-11), "-11");
    assert.equal(formatOtdDaysDiff(3), "+3");
    assert.equal(formatOtdDaysDiff(null), "—");
  });
});
