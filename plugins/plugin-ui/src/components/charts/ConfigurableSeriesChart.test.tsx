import { render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { formatSeriesChartValue, mergeSeriesChartOptions } from "./seriesChartOptions";

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

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

  it("legenda lista várias séries quando seriesList tem 2+", () => {
    render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "Jan", value: 80 },
          { label: "Fev", value: 70 },
        ]}
        seriesList={[
          {
            name: "OEE",
            points: [
              { label: "Jan", value: 80 },
              { label: "Fev", value: 70 },
            ],
          },
          {
            name: "OTD",
            points: [
              { label: "Jan", value: 90 },
              { label: "Fev", value: 95 },
            ],
          },
        ]}
        options={{ showLegend: true, legendPosition: "bottom", showTitle: false }}
      />,
    );
    expect(screen.getByText("OEE")).toBeTruthy();
    expect(screen.getByText("OTD")).toBeTruthy();
  });

  it("barras multi-série renderizam legenda agrupada", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="bar"
        points={[
          { label: "Jan", value: 10 },
          { label: "Fev", value: 20 },
        ]}
        seriesList={[
          {
            name: "A",
            points: [
              { label: "Jan", value: 10 },
              { label: "Fev", value: 20 },
            ],
          },
          {
            name: "B",
            points: [
              { label: "Jan", value: 15 },
              { label: "Fev", value: 25 },
            ],
          },
        ]}
        options={{ showLegend: true, legendPosition: "bottom", showTitle: false }}
      />,
    );
    expect(screen.getByText("A")).toBeTruthy();
    expect(screen.getByText("B")).toBeTruthy();
    expect(container.querySelectorAll("rect.delpi-ui-series-chart__series-bar, rect").length).toBeGreaterThan(2);
  });

  it("coloca box-shadow no shell (não no card com overflow:hidden)", () => {
    const shadow = "0 12px 28px rgba(15, 23, 42, 0.1)";
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "jan/26", value: 10 },
          { label: "fev/26", value: 20 },
        ]}
        options={{ title: "OEE", showLegend: false, legendPosition: "hidden" }}
        chartParts={{
          chartArea: { style: { boxShadow: shadow, borderRadius: 16 } },
        }}
      />,
    );
    const shell = container.querySelector(".delpi-ui-series-chart-shell") as HTMLElement;
    const card = container.querySelector(".delpi-ui-series-chart") as HTMLElement;
    expect(shell).toBeTruthy();
    expect(shell.style.boxShadow).toBe(shadow);
    expect(card.style.boxShadow === "" || card.style.boxShadow === "none").toBe(true);
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

  it("tabela de dados permanece no fluxo (sem position absolute por frame legado)", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[
          { label: "11/06/26", value: 66.7 },
          { label: "16/06/26", value: 86.2 },
        ]}
        options={{
          showDataTable: true,
          seriesName: "OTD — série temporal",
          showLegend: false,
          legendPosition: "hidden",
          valueFormat: "percent",
        }}
        chartParts={{
          dataTable: {
            visible: true,
            frame: { x: 0, y: 20, w: 35, h: 60 },
          },
        }}
      />,
    );
    const tableHost = container.querySelector(".delpi-ui-series-chart__data-table") as HTMLElement;
    expect(tableHost).toBeTruthy();
    expect(tableHost.style.position).not.toBe("absolute");
    expect(tableHost.querySelector("td")?.textContent).toBe("11/06/26");
    expect(tableHost.textContent).toContain("66,7%");
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

  it("pinta plotArea antes da grade (grade não fica coberta pelo fill)", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="area"
        points={[
          { label: "a", value: 90 },
          { label: "b", value: 95 },
          { label: "c", value: 88 },
          { label: "d", value: 92 },
        ]}
        options={{ showGrid: true, showLegend: false, legendPosition: "hidden" }}
      />,
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    const plot = svg!.querySelector(".delpi-ui-series-chart__plot-area");
    const grid = svg!.querySelector(".delpi-ui-series-chart__grid-line");
    expect(plot).toBeTruthy();
    expect(grid).toBeTruthy();
    const position = plot!.compareDocumentPosition(grid!);
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("aplica opacity da parte plotArea no rect SVG", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="area"
        points={[
          { label: "a", value: 90 },
          { label: "b", value: 95 },
        ]}
        options={{ showLegend: false, legendPosition: "hidden" }}
        chartParts={{
          plotArea: { visible: true, style: { fill: "#ffffff", opacity: 0 } },
        }}
      />,
    );
    const plot = container.querySelector(".delpi-ui-series-chart__plot-area");
    expect(plot).toBeTruthy();
    expect(plot!.getAttribute("opacity")).toBe("0");
  });

  it("clipa cantos arredondados da chartArea (overflow hidden na raiz)", () => {
    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[{ label: "jan/26", value: 10 }]}
        options={{ showLegend: false, legendPosition: "hidden" }}
        chartParts={{
          chartArea: {
            visible: true,
            style: { borderRadius: 16, stroke: "#b4b4b4", strokeWidth: 1, fill: "#ffffff" },
          },
        }}
      />,
    );
    const root = container.querySelector(".delpi-ui-series-chart") as HTMLElement;
    expect(root).toBeTruthy();
    expect(root.style.overflow).toBe("hidden");
    expect(root.style.borderRadius).toMatch(/16/);
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
