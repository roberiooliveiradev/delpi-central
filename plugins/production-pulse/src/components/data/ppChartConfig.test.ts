import { describe, expect, it } from "vitest";

import type { ChartPoint } from "../../utils/detailDisplay";
import {
  buildPpReadingsChartSeries,
  formatPpReadingsChartValue,
  PP_READINGS_SERIES_KEY,
  readingsToComparativeData,
  readingsToSeriesPoints,
  resolvePpReadingsChartHeight,
} from "./ppChartConfig";

const SAMPLE_POINTS: ChartPoint[] = [
  { x: "2026-09-01T19:28:56.000Z", y: 0, label: "01/09, 19:28:56" },
  { x: "2026-09-01T19:33:50.000Z", y: 1, label: "01/09, 19:33:50" },
];

describe("ppChartConfig", () => {
  it("readingsToComparativeData mapeia label e valor para Recharts", () => {
    expect(readingsToComparativeData(SAMPLE_POINTS)).toEqual([
      { name: "01/09, 19:28:56", [PP_READINGS_SERIES_KEY]: 0 },
      { name: "01/09, 19:33:50", [PP_READINGS_SERIES_KEY]: 1 },
    ]);
  });

  it("readingsToSeriesPoints mantém compatibilidade legada", () => {
    expect(readingsToSeriesPoints(SAMPLE_POINTS)).toEqual([
      { label: "01/09, 19:28:56", value: 0 },
      { label: "01/09, 19:33:50", value: 1 },
    ]);
  });

  it("buildPpReadingsChartSeries ajusta opacidade ao tema", () => {
    expect(buildPpReadingsChartSeries(false)[0]?.fillOpacity).toBe(0.45);
    expect(buildPpReadingsChartSeries(true)[0]?.fillOpacity).toBe(0.38);
  });

  it("formatPpReadingsChartValue usa locale pt-BR", () => {
    expect(formatPpReadingsChartValue(1234.5)).toMatch(/1\.234,5/);
  });

  it("resolvePpReadingsChartHeight respeita variant e override", () => {
    expect(resolvePpReadingsChartHeight("mini")).toBe(220);
    expect(resolvePpReadingsChartHeight("detail", 300)).toBe(300);
  });
});
