import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import fixtureJson from "./fixtures/chartPercentageEnrich.json";
import { TvDataSeriesChartWidget } from "./tvDataChartWidgets";

const fixture = fixtureJson as {
  source: string;
  cases: Array<{
    id: string;
    chartType: "pie" | "bar";
    chartParts?: Record<string, { visible?: boolean }>;
    points?: Array<{
      label: string;
      value: number | null;
      displayPercentageOfTotal: string | null;
    }>;
    series?: Array<{
      name: string;
      points: Array<{
        label: string;
        value: number | null;
        displayPercentageOfTotal: string | null;
      }>;
    }>;
  }>;
};

const labelOptions = {
  showDataLabels: true,
  showLegend: false,
  legendPosition: "hidden" as const,
  showTitle: false,
  dataLabels: {
    showPercentage: true,
    showValue: false,
    showCategoryName: false,
    showSeriesName: false,
  },
};

function labels(container: HTMLElement): string {
  return [...container.querySelectorAll(".delpi-ui-series-chart__data-label")]
    .map((node) => node.textContent ?? "")
    .join(" | ");
}

describe("fixture de enrich do DisplayFormatService", () => {
  it("declara a origem autoritativa", () => {
    expect(fixture.source).toBe("DisplayFormatService.apply_to_resolved");
  });

  it.each(fixture.cases.map((entry) => [entry.id, entry] as const))(
    "pinta o texto do caso %s",
    (_id, entry) => {
      const { container } = render(
        <TvDataSeriesChartWidget
          chartType={entry.chartType}
          chartOptions={labelOptions}
          chartParts={entry.chartParts}
          resolved={{
            chart: {
              points: entry.points,
              series: entry.series,
            },
          }}
        />,
      );
      const text = labels(container);
      const points = entry.points ?? entry.series?.flatMap((series) => series.points) ?? [];
      for (const point of points) {
        if (typeof point.displayPercentageOfTotal === "string") {
          expect(text).toContain(point.displayPercentageOfTotal);
        }
      }
      expect(text).not.toContain("NaN");
      expect(text).not.toContain("Infinity");
      const tokens = text.split(" | ").filter(Boolean);
      if (entry.id === "hidden-marker") {
        expect(tokens).toEqual(["100,00%"]);
      }
      if (entry.id === "zero-denominator") {
        expect(tokens).toEqual([]);
      }
      if (entry.id === "null-and-hundred") {
        expect(tokens).toEqual(["100,00%"]);
      }
    },
  );
});
