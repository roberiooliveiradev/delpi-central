#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  monthLabelPt,
  resolveYearMonthRange,
} from "./billingByCustomerMonthContent.ts";

describe("billingByCustomerMonthContent", () => {
  it("resolve ano inteiro e mês único", () => {
    assert.deepEqual(resolveYearMonthRange(2026, "all"), {
      start: "2026-01-01",
      end: "2026-12-31",
    });
    assert.deepEqual(resolveYearMonthRange(2026, 2), {
      start: "2026-02-01",
      end: "2026-02-28",
    });
  });

  it("rotula mês curto em PT", () => {
    assert.equal(monthLabelPt("2026-01"), "Jan/26");
    assert.equal(monthLabelPt("2026-12"), "Dez/26");
  });
});
