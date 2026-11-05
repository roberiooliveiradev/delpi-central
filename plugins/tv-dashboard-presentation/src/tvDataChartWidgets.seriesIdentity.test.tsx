import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TvDataSeriesChartWidget } from "./tvDataChartWidgets";

const labelOptions = {
  showDataLabels: true,
  showLegend: true,
  legendPosition: "bottom" as const,
  showTitle: false,
  showMarkers: true,
  dataLabels: {
    showPercentage: true,
    showValue: false,
    showCategoryName: false,
    showSeriesName: false,
  },
};

function parts(container: HTMLElement): string[] {
  return [...container.querySelectorAll("[data-chart-part]")].map(
    (node) => node.getAttribute("data-chart-part") ?? "",
  );
}

const ghost = {
  name: "Fantasma",
  points: [
    { label: "a", value: null },
    { label: "b", value: Number.NaN },
  ],
};

const production = {
  name: "Produção",
  points: [
    { label: "a", value: 25, displayPercentageOfTotal: "25,00%" },
    { label: "b", value: 75, displayPercentageOfTotal: "75,00%" },
  ],
};

const quality = {
  name: "Qualidade",
  plotOn: "secondary" as const,
  points: [
    { label: "a", value: 10, displayPercentageOfTotal: "50,00%" },
    { label: "b", value: 10, displayPercentageOfTotal: "50,00%" },
  ],
};

describe("identidade de série após filtrar série vazia", () => {
  it("mantém series:1 e series:2 quando a série 0 não tem número", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={labelOptions}
        chartParts={{
          "series:1": { style: { stroke: "#ff00aa" } },
          "marker:1:0": { visible: false },
          "series:2": { style: { stroke: "#00aaff" } },
        }}
        resolved={{
          chart: { series: [ghost, production, quality] },
        }}
      />,
    );
    const refs = parts(container);
    expect(refs).toContain("series:1");
    expect(refs).toContain("series:2");
    expect(refs).not.toContain("series:0");
    expect(refs.filter((ref) => ref.startsWith("marker:"))).toEqual([
      "marker:1:1",
      "marker:2:0",
      "marker:2:1",
    ]);
    expect(refs).toContain("marker:2:0");
    expect(container.querySelector('[data-chart-part="series:1"]')?.getAttribute("stroke")).toBe(
      "#ff00aa",
    );
    expect(container.querySelector('[data-chart-part="series:2"]')?.getAttribute("stroke")).toBe(
      "#00aaff",
    );
    const labels = [...container.querySelectorAll(".delpi-ui-series-chart__data-label")].map(
      (node) => node.textContent ?? "",
    );
    expect(labels.join(" ")).toContain("75,00%");
    expect(labels.join(" ")).not.toContain("25,00%");
    expect(labels.filter((text) => text.includes("50,00%"))).toHaveLength(2);
    const legend = [...container.querySelectorAll(".delpi-ui-series-chart__legend-item")];
    expect(legend.map((node) => node.textContent)).toEqual(["Produção", "Qualidade"]);
    expect(legend[0]?.getAttribute("data-chart-part")).toBe("series:1");
    expect(legend[1]?.getAttribute("data-chart-part")).toBe("series:2");
  });

  it("série oculta some sem renumerar a seguinte", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={labelOptions}
        chartParts={{ "series:1": { visible: false } }}
        resolved={{ chart: { series: [ghost, production, quality] } }}
      />,
    );
    expect(container.querySelector("polyline[data-chart-part='series:1']")).toBeNull();
    expect(container.querySelector("polyline[data-chart-part='series:2']")).toBeTruthy();
    expect(
      [...container.querySelectorAll(".delpi-ui-series-chart__legend-item")].map((node) =>
        node.getAttribute("data-chart-part"),
      ),
    ).toEqual(["series:1", "series:2"]);
    const labels = [...container.querySelectorAll(".delpi-ui-series-chart__data-label")].map(
      (node) => node.textContent ?? "",
    );
    expect(labels.join(" ")).not.toContain("25,00%");
    expect(labels.join(" ")).not.toContain("75,00%");
    expect(labels.filter((text) => text.includes("50,00%"))).toHaveLength(2);
  });

  it("série vazia no meio preserva a série seguinte", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="bar"
        chartOptions={{ ...labelOptions, showLegend: false, legendPosition: "hidden" }}
        chartParts={{ "series:2": { style: { fill: "#112233" } } }}
        resolved={{ chart: { series: [production, ghost, quality] } }}
      />,
    );
    const series = container.querySelector('[data-chart-part="series:2"]');
    expect(series).toBeTruthy();
    expect(series?.getAttribute("fill") || series?.querySelector("[fill]")?.getAttribute("fill")).toBe(
      "#112233",
    );
    expect(parts(container)).not.toContain("series:1");
  });

  it("série vazia no fim não cria índice extra", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={{ ...labelOptions, showLegend: false, legendPosition: "hidden" }}
        resolved={{ chart: { series: [production, quality, ghost] } }}
      />,
    );
    const refs = parts(container);
    expect(refs).toContain("series:0");
    expect(refs).toContain("series:1");
    expect(refs).not.toContain("series:2");
  });

  it("todas as séries vazias não pintam série", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={labelOptions}
        resolved={{ chart: { series: [ghost, ghost] } }}
      />,
    );
    expect(parts(container).some((ref) => ref.startsWith("series:"))).toBe(false);
    expect(container.textContent).toContain("Sem dados");
  });

  it("zero mantém a série; null no meio não desloca o marcador", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={{ ...labelOptions, showLegend: false, legendPosition: "hidden" }}
        chartParts={{ "marker:0:2": { visible: false } }}
        resolved={{
          chart: {
            series: [
              {
                name: "Produção",
                points: [
                  { label: "a", value: 0, displayPercentageOfTotal: "0,00%" },
                  { label: "b", value: null },
                  { label: "c", value: 10, displayPercentageOfTotal: "100,00%" },
                ],
              },
            ],
          },
        }}
      />,
    );
    const refs = parts(container);
    expect(refs).toContain("series:0");
    expect(refs).toContain("marker:0:0");
    expect(refs).not.toContain("marker:0:2");
    const labels = [...container.querySelectorAll(".delpi-ui-series-chart__data-label")].map(
      (node) => node.textContent ?? "",
    );
    expect(labels.join(" ")).toContain("0,00%");
    expect(labels.join(" ")).not.toContain("100,00%");
  });

  it("reordenar a legenda não troca o índice da série", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={{ ...labelOptions, legendSort: "nameDesc" }}
        resolved={{ chart: { series: [ghost, production, quality] } }}
      />,
    );
    const legend = [...container.querySelectorAll(".delpi-ui-series-chart__legend-item")];
    expect(legend.map((node) => node.getAttribute("data-chart-part"))).toEqual([
      "series:2",
      "series:1",
    ]);
  });

  it("uma série válida continua em series:0", () => {
    const { container } = render(
      <TvDataSeriesChartWidget
        chartType="line"
        chartOptions={{ ...labelOptions, showLegend: false, legendPosition: "hidden" }}
        resolved={{ chart: { series: [production] } }}
      />,
    );
    expect(parts(container)).toContain("series:0");
    expect(parts(container)).not.toContain("series:1");
  });
});
