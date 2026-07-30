import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { ChartAxisLines } from "./ChartAxisLines";
import type { SeriesChartLayout } from "./layout";

const layout: SeriesChartLayout = {
  width: 400,
  height: 240,
  margin: { top: 20, right: 20, bottom: 40, left: 48 },
  plotW: 332,
  plotH: 180,
  plotInset: 0,
  xLabelStep: 1,
  rotateXLabels: false,
  toX: (i, n) => 48 + (i / Math.max(1, n - 1)) * 332,
  toY: (v) => 200 - v,
  axisMin: 0,
  axisMax: 100,
  yTicks: [0, 50, 100],
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

  it("não renderiza nada quando ambos off", () => {
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} showX={false} showY={false} />
      </svg>,
    );
    expect(container.querySelectorAll('[data-axis]')).toHaveLength(0);
  });

  it("respeita visible=false como master", () => {
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} visible={false} showX showY />
      </svg>,
    );
    expect(container.querySelectorAll('[data-axis]')).toHaveLength(0);
  });
});
