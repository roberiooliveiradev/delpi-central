import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { GaugeChartView } from "./GaugeChartView";

describe("GaugeChartView chartArea / plotArea", () => {
  const model = {
    value: 98.4,
    goal: 95,
    min: 0,
    max: 100,
    label: "OTD",
    unit: "%",
    showTitle: false,
    title: "OTD",
  };

  it("usa shell + delpi-ui-series-chart e expõe plotArea no plotHost", () => {
    const { container } = render(<GaugeChartView model={model} options={{}} />);
    expect(container.querySelector(".delpi-ui-series-chart-shell")).toBeTruthy();
    const host = container.querySelector(".tdp-gauge-chart.delpi-ui-series-chart")!;
    const plot = container.querySelector(".delpi-ui-series-chart__plot-host")!;
    expect(host.getAttribute("data-chart-part")).toBe("chartArea");
    expect(host.getAttribute("data-chart-type")).toBe("gauge");
    expect(plot.getAttribute("data-chart-part")).toBe("plotArea");
    expect(container.querySelector(".tdp-gauge-chart--part-selected")).toBeNull();
  });

  it("não chama chartArea quando o alvo é uma subparte", () => {
    const onPartPointerDown = vi.fn();
    const onPartDoubleClick = vi.fn();
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        interaction={{
          onPartPointerDown,
          onPartDoubleClick,
        }}
      />,
    );
    const host = container.querySelector(".tdp-gauge-chart")!;
    const needle = container.querySelector('[data-chart-part="gaugeNeedle"]')!;
    expect(needle).toBeTruthy();

    fireEvent.pointerDown(needle);
    const chartAreaCalls = onPartPointerDown.mock.calls.filter(
      (call) => call[0]?.kind === "chartArea",
    );
    expect(chartAreaCalls).toHaveLength(0);

    fireEvent.pointerDown(host);
    expect(onPartPointerDown).toHaveBeenCalledWith(
      { kind: "chartArea" },
      expect.anything(),
    );
  });

  it("pointer no plot seleciona plotArea e não chartArea", () => {
    const onPartPointerDown = vi.fn();
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        interaction={{ onPartPointerDown }}
      />,
    );
    const plot = container.querySelector(".delpi-ui-series-chart__plot-host")!;
    fireEvent.pointerDown(plot);
    expect(onPartPointerDown).toHaveBeenCalledWith(
      { kind: "plotArea" },
      expect.anything(),
    );
    const chartAreaCalls = onPartPointerDown.mock.calls.filter(
      (call) => call[0]?.kind === "chartArea",
    );
    expect(chartAreaCalls).toHaveLength(0);
  });

  it("pointer no plot não engole subparte do velocímetro", () => {
    const onPartPointerDown = vi.fn();
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        interaction={{ onPartPointerDown }}
      />,
    );
    const needle = container.querySelector('[data-chart-part="gaugeNeedle"]')!;
    fireEvent.pointerDown(needle);
    expect(onPartPointerDown).toHaveBeenCalledWith(
      { kind: "gaugeNeedle" },
      expect.anything(),
    );
    const plotCalls = onPartPointerDown.mock.calls.filter(
      (call) => call[0]?.kind === "plotArea",
    );
    expect(plotCalls).toHaveLength(0);
  });

  it("duplo clique no fundo vazio do host seleciona chartArea", () => {
    const onPartDoubleClick = vi.fn();
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        interaction={{ onPartDoubleClick }}
      />,
    );
    const host = container.querySelector(".tdp-gauge-chart")!;
    fireEvent.doubleClick(host);
    expect(onPartDoubleClick).toHaveBeenCalledWith(
      { kind: "chartArea" },
      expect.anything(),
    );
  });

  it("aplica fill independente do plotArea via chartParts", () => {
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        chartParts={{
          plotArea: { style: { fill: "rgb(1, 2, 3)" } },
        }}
      />,
    );
    const plot = container.querySelector(".delpi-ui-series-chart__plot-host") as HTMLElement;
    expect(plot.style.background).toContain("rgb(1, 2, 3)");
  });

  it("mostra handles de resize do plotArea via ChartPlotAreaChrome", () => {
    const onPartResizePointerDown = vi.fn();
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{}}
        chartParts={{
          plotArea: { frame: { x: 10, y: 10, w: 80, h: 70 } },
        }}
        interaction={{
          selectedPart: { kind: "plotArea" },
          onPartPointerDown: () => undefined,
          onPartResizePointerDown,
        }}
      />,
    );
    const chrome = container.querySelector(
      ".delpi-ui-series-chart__plot-area-chrome",
    ) as HTMLElement;
    expect(chrome).toBeTruthy();
    expect(chrome.style.left).toBe("10%");
    expect(chrome.style.width).toBe("80%");
    expect(
      container.querySelector('[aria-label="Redimensionar canto inferior direito"]'),
    ).toBeTruthy();
  });

  it("SVG do velocímetro preenche o plotHost (sem size=260)", () => {
    const { container } = render(<GaugeChartView model={model} options={{}} />);
    const svg = container.querySelector(".tdp-speedometer-gauge__svg, .delpi-ui-speedometer-gauge__svg");
    expect(svg?.getAttribute("width")).toBe("100%");
    expect(svg?.getAttribute("height")).toBe("100%");
  });

  it("oculta legenda de faixas quando showLegend é false", () => {
    const { container } = render(
      <GaugeChartView model={model} options={{ showLegend: false }} />,
    );
    expect(container.querySelector(".tdp-speedometer-gauge__legend")).toBeNull();
  });

  it("oculta legenda quando part legend.visible é false", () => {
    const { container } = render(
      <GaugeChartView
        model={model}
        options={{ showLegend: true }}
        chartParts={{ legend: { visible: false } }}
      />,
    );
    expect(container.querySelector(".tdp-speedometer-gauge__legend")).toBeNull();
  });

  it("mostra legenda de faixas por padrão", () => {
    const { container } = render(<GaugeChartView model={model} options={{}} />);
    expect(container.querySelector(".tdp-speedometer-gauge__legend")).toBeTruthy();
  });
});
