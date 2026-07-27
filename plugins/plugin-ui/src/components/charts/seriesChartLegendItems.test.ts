import { describe, expect, it } from "vitest";

import {
  buildSeriesChartLegendItems,
  seriesChartUsesCategoryLegend,
} from "./seriesChartLegendItems";
import { OFFICE_CHART_SERIES_COLOR } from "./seriesChartOptions";

describe("seriesChartLegendItems", () => {
  it("usa legenda por categoria em pie/funnel/stacked_bar com série única", () => {
    expect(seriesChartUsesCategoryLegend("pie", 1)).toBe(true);
    expect(seriesChartUsesCategoryLegend("funnel", 1)).toBe(true);
    expect(seriesChartUsesCategoryLegend("stacked_bar", 1)).toBe(true);
    expect(seriesChartUsesCategoryLegend("pie", 2)).toBe(false);
    expect(seriesChartUsesCategoryLegend("bar", 1)).toBe(false);
    expect(seriesChartUsesCategoryLegend("line", 1)).toBe(false);
  });

  it("pizza lista LMP/AMOSTRA com cores por fatia — não o nome da série", () => {
    const items = buildSeriesChartLegendItems({
      chartType: "pie",
      seriesColor: "#089bdb",
      points: [
        { label: "LMP", value: 12, sourceIndex: 0 },
        { label: "AMOSTRA", value: 2, sourceIndex: 1 },
      ],
      categoryColors: ["#089bdb", "#22c55e"],
    });
    expect(items).toEqual([
      { name: "LMP", color: "#089bdb" },
      { name: "AMOSTRA", color: "#22c55e" },
    ]);
  });

  it("linha single-series retorna undefined (fallback seriesName)", () => {
    const items = buildSeriesChartLegendItems({
      chartType: "line",
      seriesColor: OFFICE_CHART_SERIES_COLOR,
      points: [
        { label: "Jan", value: 10, sourceIndex: 0 },
        { label: "Fev", value: 20, sourceIndex: 1 },
      ],
    });
    expect(items).toBeUndefined();
  });

  it("pizza prioriza fill do marker e chartParts na cor da legenda", () => {
    const items = buildSeriesChartLegendItems({
      chartType: "pie",
      seriesColor: "#089bdb",
      points: [
        { label: "LMP", value: 12, sourceIndex: 0 },
        { label: "AMOSTRA", value: 2, sourceIndex: 1 },
      ],
      chartParts: {
        "marker:0:1": { style: { fill: "#ff00aa" } },
      },
    });
    expect(items?.[1]?.color).toBe("#ff00aa");
  });

  it("multi-série prioriza nomes das séries", () => {
    const items = buildSeriesChartLegendItems({
      chartType: "pie",
      seriesColor: "#089bdb",
      points: [{ label: "Ignorado", value: 1, sourceIndex: 0 }],
      seriesList: [
        {
          name: "OEE",
          points: [
            { label: "Jan", value: 80, sourceIndex: 0 },
            { label: "Fev", value: 70, sourceIndex: 1 },
          ],
        },
        {
          name: "OTD",
          color: "#14b8a6",
          points: [
            { label: "Jan", value: 90, sourceIndex: 0 },
            { label: "Fev", value: 95, sourceIndex: 1 },
          ],
        },
      ],
    });
    expect(items).toEqual([
      { name: "OEE", color: expect.any(String) },
      { name: "OTD", color: "#14b8a6" },
    ]);
  });
});
