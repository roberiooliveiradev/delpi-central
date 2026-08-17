#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolvePeriodKindChip } from "./periodPreset.ts";

describe("resolvePeriodKindChip", () => {
  it("mapeia este mês para MTD e ano para YTD", () => {
    assert.equal(resolvePeriodKindChip("this_month"), "MTD");
    assert.equal(resolvePeriodKindChip("this_year"), "YTD");
    assert.equal(resolvePeriodKindChip("last_12_months"), "YTD");
    assert.equal(resolvePeriodKindChip("custom"), null);
    assert.equal(resolvePeriodKindChip("this_quarter"), null);
  });
});
