import { describe, expect, it } from "vitest";

import {
  DATE_RANGE_PRESET_OPTIONS,
  findDateRangeKeys,
  isDateRangePairKey,
} from "./dateRangePresets";

describe("dateRangePresets", () => {
  it("detecta par date_start/date_end legado", () => {
    const pair = findDateRangeKeys(["date_start", "date_end", "branch"]);
    expect(pair).toEqual({ startKey: "date_start", endKey: "date_end" });
    expect(isDateRangePairKey("date_start", pair)).toBe(true);
    expect(isDateRangePairKey("branch", pair)).toBe(false);
  });

  it("prefere start_date/end_date quando ambos os pares existem", () => {
    const pair = findDateRangeKeys([
      "date_start",
      "date_end",
      "start_date",
      "end_date",
      "branch",
    ]);
    expect(pair).toEqual({ startKey: "start_date", endKey: "end_date" });
  });

  it("expõe presets relativos e personalizado", () => {
    const values = DATE_RANGE_PRESET_OPTIONS.map((item) => item.value);
    expect(values).toContain("this_month");
    expect(values).toContain("this_month_full");
    expect(values).toContain("this_month_until_yesterday");
    expect(values).toContain("this_week");
    expect(values).toContain("this_week_full");
    expect(values).toContain("this_quarter");
    expect(values).toContain("this_quarter_full");
    expect(values).toContain("this_year");
    expect(values).toContain("this_year_full");
    expect(values).toContain("previous_day");
    expect(values).toContain("previous_month");
    expect(values).toContain("previous_year");
    expect(values).toContain("last_90_days");
    expect(values).toContain("last_n_days");
    expect(values).toContain("custom");
    expect(DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "previous_day")?.label).toBe(
      "Dia anterior",
    );
    expect(
      DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "this_month_until_yesterday")?.label,
    ).toBe("Este mês (até ontem)");
    expect(DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "this_month_full")?.label).toBe(
      "Este mês",
    );
    expect(DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "this_week_full")?.label).toBe(
      "Esta semana",
    );
    expect(DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "this_quarter_full")?.label).toBe(
      "Este trimestre",
    );
    expect(DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === "this_year_full")?.label).toBe(
      "Este ano",
    );
    // Full vem logo após o par «até hoje».
    const weekIdx = values.indexOf("this_week");
    expect(values[weekIdx + 1]).toBe("this_week_full");
    const monthIdx = values.indexOf("this_month");
    expect(values[monthIdx + 1]).toBe("this_month_full");
  });
});
