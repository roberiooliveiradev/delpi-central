import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChartViewBlockView } from "./chartViewBlockView";
import type { ComunicadoChartViewBlock } from "./comunicadoTypes";

function chartBlock(
  chartType: ComunicadoChartViewBlock["chartType"],
): ComunicadoChartViewBlock {
  return {
    id: "c1",
    type: "chart_view",
    frame: { x: 0, y: 0, w: 40, h: 30 },
    style: {},
    chartType,
    dataSourceId: "src-1",
    resolved: {
      label: "TOP 5",
      chart: {
        points: [
          { label: "CT-01", value: 120 },
          { label: "CT-02", value: 80 },
        ],
      },
    },
  };
}

describe("ChartViewBlockView", () => {
  it("horizontal_bar pinta o gráfico (não o placeholder «em breve»)", () => {
    const { container } = render(
      <ChartViewBlockView block={chartBlock("horizontal_bar")} />,
    );
    expect(screen.queryByText(/em breve/i)).toBeNull();
    expect(container.querySelector(".tdp-data-block--chart")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart")).toBeTruthy();
  });

  it("bar (colunas) continua pintando", () => {
    const { container } = render(<ChartViewBlockView block={chartBlock("bar")} />);
    expect(screen.queryByText(/em breve/i)).toBeNull();
    expect(container.querySelector(".delpi-ui-series-chart")).toBeTruthy();
  });
});
