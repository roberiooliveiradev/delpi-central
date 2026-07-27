import { render } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { ConfigurableSeriesChart } from "../ConfigurableSeriesChart";

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

describe("ChartSeriesPie pointer", () => {
  it("sem interaction não engole o clique (bubbling para o wrap do bloco)", () => {
    const parentDown = vi.fn();
    const { container } = render(
      <div onPointerDown={parentDown}>
        <ConfigurableSeriesChart
          chartType="pie"
          points={[
            { label: "LMP", value: 12 },
            { label: "AMOSTRA", value: 2 },
          ]}
          options={{ showTitle: false, showLegend: false, showAxes: false }}
        />
      </div>,
    );
    const slice = container.querySelector(".delpi-ui-series-chart__series-pie-slice");
    expect(slice).toBeTruthy();
    slice!.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
    expect(parentDown).toHaveBeenCalled();
  });

  it("com interaction para no handler da fatia (não sobe ao pai)", () => {
    const parentDown = vi.fn();
    const partDown = vi.fn();
    const { container } = render(
      <div onPointerDown={parentDown}>
        <ConfigurableSeriesChart
          chartType="pie"
          points={[
            { label: "LMP", value: 12 },
            { label: "AMOSTRA", value: 2 },
          ]}
          options={{ showTitle: false, showLegend: false, showAxes: false }}
          interaction={{
            onPartPointerDown: partDown,
          }}
        />
      </div>,
    );
    const slice = container.querySelector(".delpi-ui-series-chart__series-pie-slice");
    expect(slice).toBeTruthy();
    slice!.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
    expect(partDown).toHaveBeenCalled();
    expect(parentDown).not.toHaveBeenCalled();
  });
});
