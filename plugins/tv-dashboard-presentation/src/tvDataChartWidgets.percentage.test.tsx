import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ComunicadoChartType } from "./comunicadoTypes";
import { TvDataSeriesChartWidget } from "./tvDataChartWidgets";

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

function labelText(container: HTMLElement): string {
  return [...container.querySelectorAll(".delpi-ui-series-chart__data-label")]
    .map((node) => node.textContent ?? "")
    .join(" | ");
}

describe("TvDataSeriesChartWidget percentual autoritativo", () => {
  it("pinta a string do enrich e não o arredondamento local", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={labelOptions}
        resolved={{
          chart: {
            points: [
              {
                label: "A",
                value: 25,
                percentageOfTotal: 25,
                displayPercentageOfTotal: "25,00%",
              },
              {
                label: "B",
                value: 75,
                percentageOfTotal: 75,
                displayPercentageOfTotal: "75,00%",
              },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25,00%");
    expect(text).toContain("75,00%");
    expect(text).not.toContain("25%");
    expect(text).not.toMatch(/(?<!,)25%/);
  });

  it("null autoritativo não vira 0%", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="bar"
        chartOptions={labelOptions}
        resolved={{
          chart: {
            points: [
              {
                label: "A",
                value: 0,
                percentageOfTotal: null,
                displayPercentageOfTotal: null,
              },
            ],
          },
        }}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).not.toContain("0%");
    expect(text).not.toContain("NaN");
    expect(text).not.toContain("Infinity");
  });

  it("payload sem os campos ainda usa o fallback local", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={labelOptions}
        resolved={{
          chart: {
            points: [
              { label: "A", value: 25 },
              { label: "B", value: 75 },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25%");
    expect(text).toContain("75%");
    expect(text).not.toContain("25,00%");
  });

  it("cada série mantém o próprio percentual", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="bar"
        chartOptions={labelOptions}
        resolved={{
          chart: {
            series: [
              {
                name: "A",
                points: [
                  { label: "a1", value: 25, displayPercentageOfTotal: "25,00%" },
                  { label: "a2", value: 75, displayPercentageOfTotal: "75,00%" },
                ],
              },
              {
                name: "B",
                points: [
                  { label: "b1", value: 10, displayPercentageOfTotal: "50,00%" },
                  { label: "b2", value: 10, displayPercentageOfTotal: "50,00%" },
                ],
              },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25,00%");
    expect(text).toContain("75,00%");
    expect(text.match(/50,00%/g)?.length).toBe(2);
  });

  it("marcador oculto não faz o ponto visível recalcular a fatia", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="pie"
        chartOptions={labelOptions}
        chartParts={{ "marker:0:1": { visible: false } }}
        resolved={{
          chart: {
            points: [
              { label: "A", value: 25, displayPercentageOfTotal: "25,00%" },
              { label: "B", value: 75, displayPercentageOfTotal: "75,00%" },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25,00%");
    expect(text).not.toContain("100%");
    expect(text).not.toContain("75,00%");
  });

  it("não reescreve a precisão que o backend já materializou", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="bar"
        chartOptions={labelOptions}
        resolved={{
          chart: {
            points: [
              { label: "A", value: 25, displayPercentageOfTotal: "25,0%" },
              { label: "B", value: 75, displayPercentageOfTotal: "75,0%" },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25,0%");
    expect(text).toContain("75,0%");
    expect(text).not.toContain("25,00%");
  });

  it("compõe categoria, valor e percentual sem reformatar as strings", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={{
          ...labelOptions,
          dataLabels: {
            showCategoryName: true,
            showValue: true,
            showPercentage: true,
            separator: "comma",
          },
        }}
        resolved={{
          chart: {
            points: [
              {
                label: "Filial 01",
                value: 25,
                displayValue: "25,00",
                displayPercentageOfTotal: "25,00%",
              },
            ],
          },
        }}
      />,
    );
    expect(labelText(container)).toContain("Filial 01, 25,00, 25,00%");
  });

  it.each([
    "line",
    "bar",
    "horizontal_bar",
    "area",
    "pie",
    "doughnut",
    "funnel",
  ] satisfies ComunicadoChartType[])("preserva o texto em %s", (chartType) => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType={chartType}
        chartOptions={labelOptions}
        resolved={{
          chart: {
            points: [
              { label: "A", value: 25, displayPercentageOfTotal: "25,00%" },
              { label: "B", value: 75, displayPercentageOfTotal: "75,00%" },
            ],
          },
        }}
      />,
    );
    const text = labelText(container);
    expect(text).toContain("25,00%");
    expect(text).toContain("75,00%");
  });
});
