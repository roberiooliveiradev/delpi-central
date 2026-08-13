import { describe, expect, it } from "vitest";

import {
  allowedBillingSeriesGranularities,
  inclusiveDayCount,
  periodRangeFromBillingPreset,
} from "./billingSeriesPeriod";

const TODAY = new Date(2026, 7, 11);

describe("billingSeriesPeriod", () => {
  it("ancora presets via resolvePeriodPreset (paridade Overview)", () => {
    expect(periodRangeFromBillingPreset("today", TODAY)).toEqual({
      startDate: "2026-08-11",
      endDate: "2026-08-11",
    });
    expect(periodRangeFromBillingPreset("this_week", TODAY)).toEqual({
      startDate: "2026-08-10",
      endDate: "2026-08-11",
    });
    expect(periodRangeFromBillingPreset("this_month", TODAY)).toEqual({
      startDate: "2026-08-01",
      endDate: "2026-08-11",
    });
    expect(periodRangeFromBillingPreset("last_month", TODAY)).toEqual({
      startDate: "2026-07-01",
      endDate: "2026-07-31",
    });
    expect(periodRangeFromBillingPreset("this_quarter", TODAY)).toEqual({
      startDate: "2026-07-01",
      endDate: "2026-08-11",
    });
    expect(periodRangeFromBillingPreset("this_year", TODAY)).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-08-11",
    });
    expect(periodRangeFromBillingPreset("last_12_months", TODAY)).toEqual({
      startDate: "2025-09-01",
      endDate: "2026-08-11",
    });
  });

  it("desabilita dia quando o período passa de 93 dias", () => {
    expect(allowedBillingSeriesGranularities("2026-08-11", "2026-08-11")).toEqual([
      "day",
      "week",
      "month",
      "year",
    ]);
    expect(allowedBillingSeriesGranularities("2025-09-01", "2026-08-11")).toEqual([
      "week",
      "month",
      "year",
    ]);
    expect(inclusiveDayCount("2025-09-01", "2026-08-11")).toBeGreaterThan(93);
  });
});
