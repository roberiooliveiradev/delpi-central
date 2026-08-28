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

  it("expõe data-chart-part plotArea distinto de chartArea", () => {
    const { container } = render(
      <GaugeChartView model={model} options={{}} />,
    );
    const host = container.querySelector(".tdp-gauge-chart")!;
    const plot = container.querySelector(".tdp-gauge-chart__plot")!;
    expect(host.getAttribute("data-chart-part")).toBe("chartArea");
    expect(plot.getAttribute("data-chart-part")).toBe("plotArea");
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
    const plot = container.querySelector(".tdp-gauge-chart__plot")!;
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
    const plot = container.querySelector(".tdp-gauge-chart__plot") as HTMLElement;
    expect(plot.style.background).toContain("rgb(1, 2, 3)");
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
