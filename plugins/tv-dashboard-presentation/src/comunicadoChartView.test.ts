import { describe, expect, it } from "vitest";

import type { ComunicadoChartType } from "./comunicadoTypes";
import { chartTypeHasBasicRender, toSeriesChartKind } from "./comunicadoChartView";

const ALL_CHART_TYPES: ComunicadoChartType[] = [
  "line",
  "bar",
  "area",
  "stacked_bar",
  "pie",
  "doughnut",
  "scatter",
  "bubble",
  "radar",
  "combo",
  "waterfall",
  "funnel",
  "histogram",
];

describe("toSeriesChartKind", () => {
  it("mapeia todos os ComunicadoChartType para paint nativo", () => {
    for (const chartType of ALL_CHART_TYPES) {
      expect(toSeriesChartKind(chartType), chartType).not.toBeNull();
      expect(chartTypeHasBasicRender(chartType)).toBe(true);
    }
  });

  it("mantém identidades e aliases esperados", () => {
    expect(toSeriesChartKind("doughnut")).toBe("pie");
    expect(toSeriesChartKind("stacked_bar")).toBe("stacked_bar");
    expect(toSeriesChartKind("histogram")).toBe("histogram");
    expect(toSeriesChartKind("scatter")).toBe("scatter");
    expect(toSeriesChartKind("bubble")).toBe("bubble");
    expect(toSeriesChartKind("radar")).toBe("radar");
    expect(toSeriesChartKind("waterfall")).toBe("waterfall");
    expect(toSeriesChartKind("funnel")).toBe("funnel");
  });
});
