import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfigurableSeriesChart } from "../ConfigurableSeriesChart";
import type { SeriesChartInteraction } from "../seriesChartParts";

describe("seleção de parte sem materializar frame", () => {
  it("selecionar legenda não chama onPartFrameChange (evita absolute/reflow)", () => {
    const onPartFrameChange = vi.fn();
    const interaction: SeriesChartInteraction = {
      selectedPart: { kind: "legend" },
      onPartFrameChange,
    };
    render(
      <ConfigurableSeriesChart
        chartType="area"
        points={[
          { label: "a", value: 90 },
          { label: "b", value: 95 },
        ]}
        options={{ title: "OEE", showLegend: true, legendPosition: "bottom" }}
        interaction={interaction}
      />,
    );
    expect(onPartFrameChange).not.toHaveBeenCalled();
  });

  it("selecionar título não chama onPartFrameChange", () => {
    const onPartFrameChange = vi.fn();
    const interaction: SeriesChartInteraction = {
      selectedPart: { kind: "title" },
      onPartFrameChange,
    };
    render(
      <ConfigurableSeriesChart
        chartType="line"
        points={[{ label: "a", value: 10 }]}
        options={{ title: "Título", showLegend: false, legendPosition: "hidden" }}
        interaction={interaction}
      />,
    );
    expect(onPartFrameChange).not.toHaveBeenCalled();
  });

  it("selecionar plotArea não chama onPartFrameChange", () => {
    const onPartFrameChange = vi.fn();
    const interaction: SeriesChartInteraction = {
      selectedPart: { kind: "plotArea" },
      onPartFrameChange,
      onPartResizePointerDown: vi.fn(),
    };
    render(
      <ConfigurableSeriesChart
        chartType="area"
        points={[
          { label: "a", value: 90 },
          { label: "b", value: 95 },
        ]}
        options={{ showLegend: false, legendPosition: "hidden" }}
        interaction={interaction}
      />,
    );
    expect(onPartFrameChange).not.toHaveBeenCalled();
  });
});
