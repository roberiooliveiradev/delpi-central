import { render } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "../ConfigurableSeriesChart";
import { isSeriesChartElementApplicable, SERIES_CHART_ELEMENT_CATALOG } from "../seriesChartElementCatalog";
import type { SeriesChartKind } from "../seriesChartOptions";
import { buildSeriesChartLayout } from "./layout";

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

const SAMPLE_POINTS = [
  { label: "A", value: 10 },
  { label: "B", value: 20 },
  { label: "C", value: 15 },
  { label: "D", value: 5 },
];

const KIND_CLASS: Record<
  Exclude<SeriesChartKind, "line" | "bar" | "area" | "pie" | "combo">,
  string
> = {
  stacked_bar: ".delpi-ui-series-chart__series-stacked-bar",
  histogram: ".delpi-ui-series-chart__series-histogram",
  scatter: ".delpi-ui-series-chart__series-scatter",
  bubble: ".delpi-ui-series-chart__series-bubble",
  radar: ".delpi-ui-series-chart__series-radar",
  waterfall: ".delpi-ui-series-chart__series-waterfall",
  funnel: ".delpi-ui-series-chart__series-funnel",
};

describe("chart advanced kinds", () => {
  it("buildSeriesChartLayout continua estável com série curta", () => {
    const layout = buildSeriesChartLayout({
      points: SAMPLE_POINTS,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 220,
    });
    expect(layout.plotW).toBeGreaterThan(40);
    expect(layout.toY(20)).toBeLessThan(layout.toY(10));
  });

  it.each(Object.keys(KIND_CLASS) as Array<keyof typeof KIND_CLASS>)(
    "ConfigurableSeriesChart pinta %s",
    (chartType) => {
      const { container } = render(
        <ConfigurableSeriesChart
          chartType={chartType}
          points={SAMPLE_POINTS}
          options={{ showTitle: false, showLegend: false, showAxes: true }}
        />,
      );
      expect(container.querySelector(KIND_CLASS[chartType])).toBeTruthy();
    },
  );

  it("catálogo de eixos exclui pie/radar/funnel", () => {
    const axes = SERIES_CHART_ELEMENT_CATALOG.find((entry) => entry.id === "axes")!;
    expect(isSeriesChartElementApplicable(axes, "scatter")).toBe(true);
    expect(isSeriesChartElementApplicable(axes, "waterfall")).toBe(true);
    expect(isSeriesChartElementApplicable(axes, "pie")).toBe(false);
    expect(isSeriesChartElementApplicable(axes, "radar")).toBe(false);
    expect(isSeriesChartElementApplicable(axes, "funnel")).toBe(false);
  });
});
