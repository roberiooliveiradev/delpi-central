import { describe, expect, it } from "vitest";

import {
  buildLinearTrendValues,
  resolveCalendarBucketFraction,
  withLinearTrendField,
} from "./linearTrendSeries";

describe("buildLinearTrendValues incomplete buckets", () => {
  it("excludes incomplete fraction from fit by default", () => {
    // Complete 0,10,20 then partial 100 at fraction 0.5 — exclude ⇒ line ~ 0,10,20,30
    const trend = buildLinearTrendValues([0, 10, 20, 100], {
      incompleteBucketMode: "exclude",
      bucketFractions: [1, 1, 1, 0.5],
    });
    expect(trend[0]).toBeCloseTo(0, 6);
    expect(trend[1]).toBeCloseTo(10, 6);
    expect(trend[2]).toBeCloseTo(20, 6);
    expect(trend[3]).toBeCloseTo(30, 6);
  });

  it("weightByFraction uses full-period equivalent in the fit", () => {
    // Partial 50 at 0.5 → treat as 100; with 0,50,100 → slope 50
    const trend = buildLinearTrendValues([0, 50, 50], {
      incompleteBucketMode: "weightByFraction",
      bucketFractions: [1, 1, 0.5],
    });
    expect(trend[0]).toBeCloseTo(0, 6);
    expect(trend[1]).toBeCloseTo(50, 6);
    expect(trend[2]).toBeCloseTo(100, 6);
  });
});

describe("resolveCalendarBucketFraction", () => {
  it("returns 1 for past buckets and partial for current", () => {
    const asOf = new Date("2026-09-15T12:00:00");
    expect(resolveCalendarBucketFraction("2026-08-01", "2026-08-31", asOf)).toBe(1);
    expect(resolveCalendarBucketFraction("2026-10-01", "2026-10-31", asOf)).toBe(0);
    const mid = resolveCalendarBucketFraction("2026-09-01", "2026-09-30", asOf);
    expect(mid).toBeGreaterThan(0.4);
    expect(mid).toBeLessThan(0.6);
  });
});

describe("withLinearTrendField", () => {
  it("reads fractionKey from rows", () => {
    const rows = [
      { v: 0, f: 1 },
      { v: 10, f: 1 },
      { v: 20, f: 1 },
      { v: 100, f: 0.5 },
    ];
    const out = withLinearTrendField(rows, "v", "_t", {
      incompleteBucketMode: "exclude",
      fractionKey: "f",
    });
    expect(out[3]._t).toBeCloseTo(30, 6);
  });
});
