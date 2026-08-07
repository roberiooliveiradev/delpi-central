import { describe, expect, it } from "vitest";

import {
  applySeriesChartLegendSort,
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
      sort: "data",
    });
    expect(items).toEqual([
      { name: "LMP", color: "#089bdb" },
      { name: "AMOSTRA", color: "#22c55e" },
    ]);
  });

  it("applySeriesChartLegendSort — pizza auto ordena valor ↓ e preserva cores via sourceIndex", () => {
    const sorted = applySeriesChartLegendSort({
      chartType: "pie",
      sort: "auto",
      points: [
        { label: "M3", value: 8.45, sourceIndex: 2 },
        { label: "FM", value: 102.04, sourceIndex: 0 },
        { label: "FH", value: 41.91, sourceIndex: 1 },
      ],
    });
    expect(sorted.resolvedSort).toBe("valueDesc");
    expect(sorted.points.map((p) => p.label)).toEqual(["FM", "FH", "M3"]);
    const items = buildSeriesChartLegendItems({
      chartType: "pie",
      seriesColor: "#089bdb",
      points: sorted.points,
      categoryColors: ["#089bdb", "#14b8a6", "#f97316"],
      sort: "data",
    });
    expect(items?.map((item) => item.name)).toEqual(["FM", "FH", "M3"]);
    expect(items?.[0]?.color).toBe("#089bdb");
    expect(items?.[2]?.color).toBe("#f97316");
  });

  it("applySeriesChartLegendSort — barra nameAsc ordena categorias no eixo X", () => {
    const sorted = applySeriesChartLegendSort({
      chartType: "bar",
      sort: "nameAsc",
      points: [
        { label: "CT-08B", value: 105.4, sourceIndex: 0 },
        { label: "CT-01B", value: 97.7, sourceIndex: 1 },
        { label: "CT-01A", value: 88.2, sourceIndex: 2 },
      ],
    });
    expect(sorted.resolvedSort).toBe("nameAsc");
    expect(sorted.points.map((p) => p.label)).toEqual(["CT-01A", "CT-01B", "CT-08B"]);
  });

  it("applySeriesChartLegendSort — multi-série nameAsc alinha categorias em todas as séries", () => {
    const sorted = applySeriesChartLegendSort({
      chartType: "bar",
      sort: "nameAsc",
      points: [],
      seriesList: [
        {
          name: "Filial 01",
          points: [
            { label: "CT-02", value: 10, sourceIndex: 0 },
            { label: "CT-01", value: 20, sourceIndex: 1 },
          ],
        },
        {
          name: "Filial 02",
          points: [
            { label: "CT-02", value: 30, sourceIndex: 0 },
            { label: "CT-01", value: 40, sourceIndex: 1 },
          ],
        },
      ],
    });
    expect(sorted.seriesList?.[0]?.points.map((p) => p.label)).toEqual(["CT-01", "CT-02"]);
    expect(sorted.seriesList?.[1]?.points.map((p) => p.value)).toEqual([40, 30]);
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
      sort: "data",
    });
    expect(items?.[1]?.color).toBe("#ff00aa");
  });

  it("multi-série prioriza nomes das séries e pode ordenar só a legenda", () => {
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
      sort: "nameDesc",
    });
    expect(items).toEqual([
      { name: "OTD", color: "#14b8a6" },
      { name: "OEE", color: expect.any(String) },
    ]);
  });
});
