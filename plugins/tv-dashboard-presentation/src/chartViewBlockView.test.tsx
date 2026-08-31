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

  it("lista vazia com bake de buckets mostra Sem dados (não card KPI)", () => {
    const block: ComunicadoChartViewBlock = {
      id: "c-empty",
      type: "chart_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      style: {},
      chartType: "bar",
      dataSourceId: "src-1",
      chartProjection: {
        categoryField: "periodo",
        series: [{ field: "total_qty", label: "Quantidade total", aggregation: "sum" }],
      },
      resolved: {
        serverProjectionApplied: true,
        kpi: { value: 5, label: "Buckets quantidade" },
        kpiMetrics: [{ field: "buckets_count", label: "Buckets quantidade", value: 5 }],
        chart: {
          points: [{ label: "Buckets quantidade", value: 5 }],
          chartType: "bar",
        },
        table: { columns: [], rows: [] },
      },
    };
    render(<ChartViewBlockView block={block} />);
    expect(screen.getByText("Sem dados")).toBeTruthy();
    expect(screen.queryByText("Buckets quantidade")).toBeNull();
  });
});
