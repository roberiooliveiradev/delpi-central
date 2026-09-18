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
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-bar").length).toBe(2);
    });
    expect(container.querySelector(".recharts-line")).toBeFalsy();
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
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-bar").length).toBe(2);
    });
  });

  it("sibling: plotAs line na série secundária continua linha", async () => {
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
      expect(container.querySelector(".recharts-line")).toBeTruthy();
    });
    expect(container.querySelectorAll(".recharts-bar").length).toBe(1);
  });

  it("positive: tendência gera uma linha por série atual, inclusive no eixo direito", async () => {
    stubChartHostSize();
    const { container } = render(
      <MultiTypeSeriesChart
        data={POINTS}
        categoryKey="periodo"
        chartType="column"
        height={320}
        showTrend
        secondaryDataKeys={["quantidade"]}
        series={[
          {
            dataKey: "faturamento",
            name: "Faturamento",
            fill: "#089bdb",
            trendSource: true,
          },
          {
            dataKey: "quantidade",
            name: "Quantidade fornecida",
            fill: "#ea580c",
            axis: "secondary",
            trendSource: true,
          },
        ]}
      />,
    );
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-line").length).toBe(2);
    });
    expect(container.textContent).toMatch(/Tendência \(Faturamento\)/);
    expect(container.textContent).toMatch(/Tendência \(Quantidade fornecida\)/);
  });

  it("sibling: tendências de série atual e comparativa coexistuem com nomes distintos", async () => {
    stubChartHostSize();
    const { container } = render(
      <MultiTypeSeriesChart
        data={[
          { periodo: "Out.", faturamento: 10, faturamento_prior: 20 },
          { periodo: "Nov.", faturamento: 20, faturamento_prior: 18 },
          { periodo: "Dez.", faturamento: 30, faturamento_prior: 16 },
        ]}
        categoryKey="periodo"
        chartType="column"
        height={320}
        showTrend
        series={[
          {
            dataKey: "faturamento",
            name: "Faturamento · Bruto",
            fill: "#089bdb",
            trendSource: true,
          },
          {
            dataKey: "faturamento_prior",
            name: "Ano ant.",
            fill: "#94a3b8",
            trendSource: true,
            trendApplyIncompleteBucket: false,
          },
        ]}
      />,
    );
    await waitFor(() => {
      expect(container.querySelectorAll(".recharts-line").length).toBe(2);
    });
    expect(container.textContent).toMatch(/Tendência \(Faturamento · Bruto\)/);
    expect(container.textContent).toMatch(/Tendência \(Ano ant\.\)/);
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
