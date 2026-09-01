import { describe, expect, it } from "vitest";

import { resolveMonthComparison } from "./monthComparison";

describe("resolveMonthComparison", () => {
  it("marks a higher expense as negative", () => {
    const comparison = resolveMonthComparison(1100, 1000);
    expect(comparison).toEqual({ deltaAmount: 100, deltaPct: 10, tone: "negative" });
  });

  it("marks a lower expense as positive", () => {
    const comparison = resolveMonthComparison(800, 1000);
    expect(comparison).toEqual({ deltaAmount: -200, deltaPct: -20, tone: "positive" });
  });

  it("leaves the tone undefined when nothing changed", () => {
    expect(resolveMonthComparison(1000, 1000)?.tone).toBeUndefined();
  });

  it("hides the percentage when the previous month has no base", () => {
    expect(resolveMonthComparison(500, 0)).toEqual({
      deltaAmount: 500,
      deltaPct: null,
      tone: "negative",
    });
  });

  it("returns null when either side is missing", () => {
    expect(resolveMonthComparison(null, 1000)).toBeNull();
    expect(resolveMonthComparison(1000, undefined)).toBeNull();
  });

  it("inverts the tone for higher_is_better metrics", () => {
    expect(resolveMonthComparison(1100, 1000, "higher_is_better")?.tone).toBe("positive");
    expect(resolveMonthComparison(900, 1000, "higher_is_better")?.tone).toBe("negative");
  });
});
