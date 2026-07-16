import { describe, expect, it } from "vitest";

import {
  DATE_RANGE_PRESET_OPTIONS,
  findDateRangeKeys,
  isDateRangePairKey,
} from "./dateRangePresets";

describe("dateRangePresets", () => {
  it("detecta par date_start/date_end", () => {
    const pair = findDateRangeKeys(["date_start", "date_end", "branch"]);
    expect(pair).toEqual({ startKey: "date_start", endKey: "date_end" });
    expect(isDateRangePairKey("date_start", pair)).toBe(true);
    expect(isDateRangePairKey("branch", pair)).toBe(false);
  });

  it("expõe presets relativos e personalizado", () => {
    const values = DATE_RANGE_PRESET_OPTIONS.map((item) => item.value);
    expect(values).toContain("this_month");
    expect(values).toContain("this_week");
    expect(values).toContain("this_quarter");
    expect(values).toContain("this_year");
    expect(values).toContain("previous_month");
    expect(values).toContain("previous_year");
    expect(values).toContain("last_90_days");
    expect(values).toContain("last_n_days");
    expect(values).toContain("custom");
  });
});
