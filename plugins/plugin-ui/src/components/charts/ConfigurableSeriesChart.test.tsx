import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { formatSeriesChartValue, mergeSeriesChartOptions } from "./seriesChartOptions";

describe("ConfigurableSeriesChart", () => {
  it("renderiza título e legenda configuráveis", () => {
    render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "jan/26", value: 630000 },
          { label: "fev/26", value: 720000 },
        ]}
        options={{
          title: "ROL",
          showTitle: true,
          seriesName: "Receita",
          showLegend: true,
          legendPosition: "bottom",
          valueFormat: "currency",
        }}
      />,
    );
    expect(screen.getByText("ROL")).toBeTruthy();
    expect(screen.getByText("Receita")).toBeTruthy();
  });

  it("renderiza tabela de dados quando habilitada", () => {
    render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "jan/26", value: 100 },
          { label: "fev/26", value: 200 },
        ]}
        options={{ showDataTable: true, seriesName: "ROL", showLegend: false, legendPosition: "hidden" }}
      />,
    );
    expect(screen.getByRole("table")).toBeTruthy();
    expect(screen.getAllByText("jan/26").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ROL").length).toBeGreaterThan(0);
  });

  it("aplica classes modulares nos elementos do gráfico", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "jan/26", value: 630000 },
          { label: "fev/26", value: 720000 },
        ]}
        options={{
          title: "OTD — série temporal",
          showTitle: true,
          seriesName: "OTD",
          showLegend: true,
          legendPosition: "bottom",
          showDataLabels: true,
          showMarkers: true,
        }}
      />,
    );

    expect(container.querySelector(".delpi-ui-series-chart__title")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__legend")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__series-line")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__series-marker")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__data-label")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__grid-line")).toBeTruthy();
  });

  it("omite marcadores quando desabilitados", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[{ label: "jan/26", value: 10 }]}
        options={{ showMarkers: false, showLegend: false, legendPosition: "hidden" }}
      />,
    );

    expect(container.querySelector(".delpi-ui-series-chart__series-marker")).toBeNull();
    expect(container.querySelector(".delpi-ui-series-chart__series-line")).toBeTruthy();
  });
});

describe("formatSeriesChartValue", () => {
  it("formata moeda em pt-BR", () => {
    const formatted = formatSeriesChartValue(1400000, "currency");
    expect(formatted).toContain("R$");
    expect(formatted).toContain("1.400.000");
  });
});

describe("mergeSeriesChartOptions", () => {
  it("aplica defaults", () => {
    const merged = mergeSeriesChartOptions({ showDataLabels: true });
    expect(merged.showGrid).toBe(true);
    expect(merged.showDataLabels).toBe(true);
  });
});
