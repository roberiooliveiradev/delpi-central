import { describe, expect, it } from "vitest";

import {
  chartTypesForFamily,
  defaultChartTypeForFamily,
  familySupportsChartTypeSwitch,
} from "./chartDataFamilies";

describe("chartDataFamilies", () => {
  it("série temporal multi não inclui pizza", () => {
    expect(chartTypesForFamily("time_multi_series")).toEqual([
      "column",
      "line",
      "area",
    ]);
    expect(familySupportsChartTypeSwitch("time_multi_series")).toBe(true);
  });

  it("ranking omite pizza acima de 12 categorias", () => {
    expect(chartTypesForFamily("ranking", { categoryCount: 20 })).toEqual([
      "horizontal_bar",
      "bar",
    ]);
    expect(chartTypesForFamily("ranking", { categoryCount: 5 })).toContain("pie");
  });

  it("funnel/scalar sem switcher", () => {
    expect(chartTypesForFamily("funnel")).toEqual([]);
    expect(familySupportsChartTypeSwitch("funnel")).toBe(false);
    expect(defaultChartTypeForFamily("funnel")).toBeUndefined();
  });
});
