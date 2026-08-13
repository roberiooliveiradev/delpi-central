import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isPriorYearCompareAllowed,
  mergeSeriesWithPriorYear,
  shiftIsoDateByYears,
  shiftPeriodRangeByYears,
} from "./periodShift.ts";

describe("periodShift", () => {
  it("shiftIsoDateByYears clamps leap day", () => {
    assert.equal(shiftIsoDateByYears("2024-02-29", -1), "2023-02-28");
    assert.equal(shiftIsoDateByYears("2024-02-29", 1), "2025-02-28");
  });

  it("shiftIsoDateByYears shifts ordinary dates", () => {
    assert.equal(shiftIsoDateByYears("2026-08-13", -1), "2025-08-13");
    assert.equal(shiftIsoDateByYears("2026-01-01", -1), "2025-01-01");
  });

  it("shiftPeriodRangeByYears shifts MTD and YTD style ranges", () => {
    assert.deepEqual(
      shiftPeriodRangeByYears(
        { start_date: "2026-08-01", end_date: "2026-08-13" },
        -1,
      ),
      { start_date: "2025-08-01", end_date: "2025-08-13" },
    );
    assert.deepEqual(
      shiftPeriodRangeByYears(
        { start_date: "2026-01-01", end_date: "2026-08-13" },
        -1,
      ),
      { start_date: "2025-01-01", end_date: "2025-08-13" },
    );
  });

  it("isPriorYearCompareAllowed blocks day granularity", () => {
    assert.equal(isPriorYearCompareAllowed("day"), false);
    assert.equal(isPriorYearCompareAllowed("week"), true);
    assert.equal(isPriorYearCompareAllowed("month"), true);
    assert.equal(isPriorYearCompareAllowed("year"), true);
  });

  it("mergeSeriesWithPriorYear aligns by index", () => {
    const current = [
      { periodo: "jan/2026", sort_key: "2026-01", value: 10 },
      { periodo: "fev/2026", sort_key: "2026-02", value: 20 },
    ];
    const prior = [{ periodo: "jan/2025", sort_key: "2025-01", value: 7 }];
    const merged = mergeSeriesWithPriorYear(current, prior, (p) => ({
      value_prior: p?.value ?? null,
    }));
    assert.equal(merged.length, 2);
    assert.equal(merged[0].periodo, "jan/2026");
    assert.equal(merged[0].value, 10);
    assert.equal(merged[0].value_prior, 7);
    assert.equal(merged[1].value_prior, null);
  });
});
