import { describe, expect, it } from "vitest";

import {
  patchChartSeriesAppearance,
  resolveChartSeriesAppearanceColor,
  resolveChartSeriesColorIndex,
} from "./chartSeriesAppearance";

describe("chartSeriesAppearance", () => {
  it("resolve prioriza projection.series[N].color", () => {
    expect(
      resolveChartSeriesAppearanceColor(
        {
          chartProjection: {
            series: [{ field: "a", color: "#111111" }, { field: "b", color: "#222222" }],
          },
          chartParts: { "series:1": { style: { stroke: "#999999" } } },
          chartOptions: { seriesColor: "#000000" },
        },
        1,
      ),
    ).toBe("#222222");
  });

  it("resolve cai em chartParts e depois seriesColor legado (índice 0)", () => {
    expect(
      resolveChartSeriesAppearanceColor(
        {
          chartParts: { "series:0": { style: { stroke: "#abcdef" } } },
          chartOptions: { seriesColor: "#ffffff" },
        },
        0,
      ),
    ).toBe("#abcdef");
    expect(
      resolveChartSeriesAppearanceColor(
        {
          chartOptions: { seriesColor: "#ff00aa" },
        },
        0,
      ),
    ).toBe("#ff00aa");
  });

  it("patch grava cor na série N em projection + parts", () => {
    const next = patchChartSeriesAppearance(
      {
        chartProjection: {
          categoryField: "mes",
          series: [{ field: "oee", label: "OEE" }, { field: "meta", label: "Meta" }],
        },
        chartParts: {},
        chartOptions: {},
      },
      1,
      { color: "#089bdb", strokeWidth: 3 },
    );
    expect(next.chartProjection?.series?.[1]?.color).toBe("#089bdb");
    expect(next.chartParts?.["series:1"]?.style?.stroke).toBe("#089bdb");
    expect(next.chartParts?.["series:1"]?.style?.strokeWidth).toBe(3);
    expect(next.chartOptions?.seriesColor).toBeUndefined();
  });

  it("patch na série 0 também atualiza seriesColor legado", () => {
    const next = patchChartSeriesAppearance(
      {
        chartProjection: { series: [{ field: "oee" }] },
        chartParts: {},
        chartOptions: { seriesColor: "#000" },
      },
      0,
      { color: "#112233" },
    );
    expect(next.chartOptions?.seriesColor).toBe("#112233");
  });

  it("patch em pizza sincroniza categoryColors e marker da fatia", () => {
    const next = patchChartSeriesAppearance(
      {
        chartType: "pie",
        chartProjection: {
          series: [{ field: "qtd", label: "Qtd" }],
        },
        chartParts: {},
        chartOptions: {},
      },
      1,
      { color: "#ff5500" },
    );
    expect(next.chartOptions?.categoryColors?.[1]).toBe("#ff5500");
    expect(next.chartParts?.["marker:0:1"]?.style?.fill).toBe("#ff5500");
    expect(next.chartParts?.["series:1"]?.style?.fill).toBe("#ff5500");
  });
});

describe("resolveChartSeriesColorIndex", () => {
  it("série e fatia usam o índice certo; legenda cai em 0", () => {
    expect(resolveChartSeriesColorIndex({ kind: "series", seriesIndex: 2 })).toBe(2);
    expect(resolveChartSeriesColorIndex({ kind: "marker", seriesIndex: 0, pointIndex: 3 })).toBe(3);
    expect(resolveChartSeriesColorIndex({ kind: "legend" })).toBe(0);
    expect(resolveChartSeriesColorIndex(null)).toBe(0);
  });
});
