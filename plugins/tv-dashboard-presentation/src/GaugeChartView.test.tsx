import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { GaugeChartView } from "./GaugeChartView";

describe("GaugeChartView chartArea guard", () => {
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
    // Subparte dispara o próprio bind; host não deve receber chartArea por bubble
    // (needle stopPropagation no bindChartPartPointer).
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

  it("duplo clique no fundo vazio seleciona chartArea", () => {
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
});
