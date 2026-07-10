import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { formatSeriesChartValue, mergeComunicadoChartOptions } from "./comunicadoChartOptions";

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
});

describe("formatSeriesChartValue", () => {
  it("formata moeda em pt-BR", () => {
    const formatted = formatSeriesChartValue(1400000, "currency");
    expect(formatted).toContain("R$");
    expect(formatted).toContain("1.400.000");
  });
});

describe("mergeComunicadoChartOptions", () => {
  it("aplica defaults", () => {
    const merged = mergeComunicadoChartOptions({ showDataLabels: true });
    expect(merged.showGrid).toBe(true);
    expect(merged.showDataLabels).toBe(true);
  });
});
