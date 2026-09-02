import { describe, expect, it } from "vitest";

import type { ChartPoint } from "../../utils/detailDisplay";
import {
  buildPpReadingsChartOptions,
  readingsToSeriesPoints,
} from "./ppChartConfig";

const SAMPLE_POINTS: ChartPoint[] = [
  { x: "2026-09-01T19:28:56.000Z", y: 0, label: "01/09, 19:28:56" },
  { x: "2026-09-01T19:33:50.000Z", y: 1, label: "01/09, 19:33:50" },
];

describe("ppChartConfig", () => {
  it("readingsToSeriesPoints mapeia label e valor", () => {
    expect(readingsToSeriesPoints(SAMPLE_POINTS)).toEqual([
      { label: "01/09, 19:28:56", value: 0 },
      { label: "01/09, 19:33:50", value: 1 },
    ]);
  });

  it("buildPpReadingsChartOptions usa área suave e tema explícito", () => {
    expect(buildPpReadingsChartOptions("mini", "dark")).toMatchObject({
      smoothLines: true,
      areaFillGradient: true,
      markerMode: "last",
      theme: "dark",
    });
    expect(buildPpReadingsChartOptions("detail", "light")).toMatchObject({
      markerMode: "all",
      theme: "light",
    });
  });
});
