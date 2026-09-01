import { describe, expect, it } from "vitest";

import {
  billingSeriesKeys,
  clampPercent,
  waterfallBarWidth,
  waterfallPeak,
} from "./billingPresentation";

describe("billingPresentation", () => {
  it("clamps attainment to 0–100 for the meter", () => {
    expect(clampPercent(90.91)).toBe(90.91);
    expect(clampPercent(140)).toBe(100);
    expect(clampPercent(-8)).toBe(0);
    expect(clampPercent(null)).toBe(0);
  });

  it("selects series keys by unit", () => {
    expect(billingSeriesKeys("01")).toEqual(["rol01"]);
    expect(billingSeriesKeys("02")).toEqual(["rol02"]);
    expect(billingSeriesKeys("all")).toEqual(["rol01", "rol02"]);
  });

  it("sizes waterfall bars from the peak line", () => {
    const peak = waterfallPeak([
      { key: "gross", label: "Bruto", value: 100, role: "add" },
      { key: "tax", label: "Imposto", value: 25, role: "subtract" },
    ]);
    expect(peak).toBe(100);
    expect(waterfallBarWidth(25, peak)).toBe(25);
    expect(waterfallBarWidth(0, peak)).toBe(0);
    expect(waterfallBarWidth(1, peak)).toBe(6);
  });
});
