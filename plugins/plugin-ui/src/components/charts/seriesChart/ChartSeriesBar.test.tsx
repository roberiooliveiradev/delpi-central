import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "../ConfigurableSeriesChart";
import { buildSeriesChartLayout } from "./layout";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartFrame } from "./ChartFrame";

describe("ChartSeriesBar overflow", () => {
  it("mantém barras dentro do plot mesmo com valor acima do eixo", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { value: 10, label: "a", sourceIndex: 0 },
        { value: 50, label: "b", sourceIndex: 1 },
        { value: 100, label: "c", sourceIndex: 2 },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
    });

    const { container } = render(
      <ChartFrame viewW={layout.viewW} viewH={layout.viewH} ariaLabel="teste">
        <ChartSeriesBar
          layout={layout}
          points={[
            { value: 10, label: "a", sourceIndex: 0 },
            { value: 50, label: "b", sourceIndex: 1 },
            // valor além do domínio — deve clamp e não furar o topo do plot
            { value: layout.axisMax * 2, label: "c", sourceIndex: 2 },
          ]}
          seriesColor="#089bdb"
        />
      </ChartFrame>,
    );

    const bars = Array.from(container.querySelectorAll("rect"));
    expect(bars.length).toBe(3);
    const plotTop = layout.margin.top;
    const plotBottom = layout.margin.top + layout.plotH;
    for (const bar of bars) {
      const y = Number(bar.getAttribute("y"));
      const height = Number(bar.getAttribute("height"));
      expect(y).toBeGreaterThanOrEqual(plotTop - 0.01);
      expect(y + height).toBeLessThanOrEqual(plotBottom + 0.01);
    }
  });

  it("aplica clipPath da área de plot no gráfico de barras", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="bar"
        points={[
          { label: "12/06", value: 80 },
          { label: "15/06", value: 120 },
          { label: "18/06", value: 95 },
        ]}
        options={{ showLegend: false, legendPosition: "hidden", title: "OEE" }}
      />,
    );

    const clip = container.querySelector("clipPath");
    expect(clip).toBeTruthy();
    const clipped = container.querySelector("g[clip-path]");
    expect(clipped).toBeTruthy();
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("overflow")).toBe("hidden");
  });
});
