import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { ChartAxisLines } from "./ChartAxisLines";
import type { SeriesChartLayout } from "./layout";

const layout: SeriesChartLayout = {
  viewW: 400,
  viewH: 240,
  margin: { top: 20, right: 20, bottom: 40, left: 48 },
  plotW: 332,
  plotH: 180,
  plotInset: 0,
  categoryScale: "band",
  orientation: "vertical",
  ticks: [0, 50, 100],
  axisMin: 0,
  axisMax: 100,
  axisRange: 100,
  xLabelStep: 1,
  xLabelsRotated: false,
  categoryLabelRotationDeg: 0,
  categoryLabelOverflow: "skip",
  visibleXLabelIndices: [0, 1],
  toX: (i, n) => 48 + (i / Math.max(1, n - 1)) * 332,
  categoryBandStart: (i) => 48 + i * 40,
  categoryBandWidth: () => 32,
  toY: (v) => 200 - v,
};

describe("ChartAxisLines", () => {
  it("não renderiza linha X quando showX=false", () => {
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} showX={false} showY />
      </svg>,
    );
    expect(container.querySelector('[data-axis="x"]')).toBeNull();
    expect(container.querySelector('[data-axis="y"]')).not.toBeNull();
  });

  it("não renderiza linha Y quando showY=false", () => {
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} showX showY={false} />
      </svg>,
    );
    expect(container.querySelector('[data-axis="x"]')).not.toBeNull();
    expect(container.querySelector('[data-axis="y"]')).toBeNull();
  });

  it("renderiza ambos os eixos por default", () => {
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} />
      </svg>,
    );
    expect(container.querySelector('[data-axis="x"]')).not.toBeNull();
    expect(container.querySelector('[data-axis="y"]')).not.toBeNull();
  });
});
