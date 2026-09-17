import { render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MultiTypeSeriesChart } from "./MultiTypeSeriesChart";

const POINTS = [
  { periodo: "Fev. de 26", faturamento: 151000, quantidade: 554.47 },
  { periodo: "Mar. de 26", faturamento: 220000, quantidade: 800 },
];

describe("MultiTypeSeriesChart dual Y", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  function stubChartHostSize() {
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(800);
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(320);
    class MockRO {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("ResizeObserver", MockRO);
  }

  it("positive: Ambos marca dual-y e desenha dois eixos Y", async () => {
    stubChartHostSize();
    const { container } = render(
      <MultiTypeSeriesChart
        data={POINTS}
        categoryKey="periodo"
        chartType="column"
        height={320}
        formatY={(value) => `R$ ${value}`}
        formatYSecondary={(value) => String(value)}
        secondaryDataKeys={["quantidade"]}
        series={[
          { dataKey: "faturamento", name: "Faturamento", fill: "#089bdb" },
          {
            dataKey: "quantidade",
            name: "Quantidade fornecida",
            fill: "#ea580c",
            axis: "secondary",
            plotAs: "line",
          },
        ]}
      />,
    );
    await waitFor(() => {
      expect(
        container.querySelector(".delpi-ui-multi-type-series-chart--dual-y"),
      ).toBeTruthy();
    });
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-yAxis").length).toBe(2);
    });
  });

  it("sibling: secondaryDataKeys sozinho ainda abre o eixo direito", async () => {
    stubChartHostSize();
    const { container } = render(
      <MultiTypeSeriesChart
        data={POINTS}
        categoryKey="periodo"
        chartType="column"
        height={320}
        secondaryDataKeys={["quantidade"]}
        series={[
          { dataKey: "faturamento", name: "Faturamento", fill: "#089bdb" },
          { dataKey: "quantidade", name: "Quantidade fornecida", fill: "#ea580c" },
        ]}
      />,
    );
    await waitFor(() => {
      expect(
        container.querySelector(".delpi-ui-multi-type-series-chart--dual-y"),
      ).toBeTruthy();
    });
  });

  it("negative: uma série em R$ não marca dual-y", async () => {
    stubChartHostSize();
    const { container } = render(
      <MultiTypeSeriesChart
        data={POINTS}
        categoryKey="periodo"
        chartType="column"
        height={320}
        series={[{ dataKey: "faturamento", name: "Faturamento", fill: "#089bdb" }]}
      />,
    );
    await waitFor(() => {
      expect(container.querySelector(".delpi-ui-multi-type-series-chart")).toBeTruthy();
    });
    expect(container.querySelector(".delpi-ui-multi-type-series-chart--dual-y")).toBeFalsy();
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-yAxis").length).toBe(1);
    });
  });
});
