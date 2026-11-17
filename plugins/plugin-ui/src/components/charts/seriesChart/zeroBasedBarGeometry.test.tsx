import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";

import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartAxisLines } from "./ChartAxisLines";
import { buildSeriesChartLayout } from "./layout";
import { ensureSelectableBarSpan, resolveZeroBasedValueSpan } from "./zeroBasedBarGeometry";

afterEach(() => cleanup());

const data = [
  { label: "01/2026", value: -1982.03 },
  { label: "02/2026", value: -61519.33 },
  { label: "03/2026", value: -106009.34 },
  { label: "05/2026", value: 16241.49 },
  { label: "07/2026", value: 85251.73 },
  { label: "11/2026", value: -781891.44 },
];

function numericAttr(element: Element, attr: string): number {
  return Number(element.getAttribute(attr));
}

describe("GLPI #1598: barras com polaridade e escala corretas", () => {
  it("ancora barras mistas no zero e representa valores negativos abaixo do eixo", () => {
    const layout = buildSeriesChartLayout({
      points: data,
      axisValues: data.map((p) => p.value),
      categoryScale: "band",
      showXAxisLabels: true,
      showYAxisLabels: true,
      showXAxisTitle: false,
      showYAxisTitle: false,
      viewW: 980,
      viewH: 470,
    });
    const zero = layout.toY(0);
    expect(layout.axisMin).toBeLessThan(0);
    expect(layout.axisMax).toBeGreaterThan(0);
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} zeroValueBaseline />
        <ChartSeriesBar layout={layout} points={data} seriesColor="#0a98d1" />
      </svg>,
    );
    const xAxis = container.querySelector('line[data-axis="x"]');
    expect(xAxis).not.toBeNull();
    expect(numericAttr(xAxis!, "y1")).toBeCloseTo(zero, 4);

    const bars = container.querySelectorAll("rect.delpi-ui-series-chart__series-bar");
    expect(bars).toHaveLength(data.length);
    for (let i = 0; i < data.length; i++) {
      const value = data[i]!.value;
      const bar = bars[i]!;
      const top = numericAttr(bar, "y");
      const height = numericAttr(bar, "height");
      const end = top + height;
      expect(height).toBeGreaterThan(0);
      if (value < 0) {
        expect(top).toBeCloseTo(zero, 4);
        expect(end).toBeCloseTo(layout.toY(value), 4);
      } else {
        expect(top).toBeCloseTo(layout.toY(value), 4);
        expect(end).toBeCloseTo(zero, 4);
      }
    }
    // Pequena perda de janeiro não pode ter a mesma altura da enorme
    // perda de novembro (bug original: barras partiam do mínimo do eixo).
    expect(numericAttr(bars[0]!, "height")).toBeLessThan(
      numericAttr(bars[5]!, "height") / 200,
    );
  });

  it("usa zero também quando TODAS as colunas são negativas", () => {
    const points = [{ label: "A", value: -10 }, { label: "B", value: -100 }];
    const layout = buildSeriesChartLayout({
      points, axisValues: points.map((p) => p.value),
      categoryScale: "band", showXAxisLabels: true,
      showXAxisTitle: false, viewW: 400, viewH: 250,
    });
    expect(layout.axisMax).toBeGreaterThanOrEqual(0);
    const zero = layout.toY(0);
    const { container } = render(
      <svg><ChartSeriesBar layout={layout} points={points} seriesColor="#0a98d1" /></svg>,
    );
    const bars = container.querySelectorAll("rect.delpi-ui-series-chart__series-bar");
    expect(numericAttr(bars[0]!, "y")).toBeCloseTo(zero);
    expect(numericAttr(bars[1]!, "y")).toBeCloseTo(zero);
    expect(numericAttr(bars[0]!, "height")).toBeLessThan(numericAttr(bars[1]!, "height"));
  });

  it("preserva barras horizontais dos dois sinais desde zero", () => {
    const points = [{ label: "Falta", value: -40 }, { label: "Sobra", value: 20 }];
    const layout = buildSeriesChartLayout({
      points, axisValues: [-40, 20],
      categoryScale: "band", orientation: "horizontal",
      showXAxisLabels: true, showXAxisTitle: false,
      viewW: 530, viewH: 250,
    });
    const zero = layout.toValueX!(0);
    const { container } = render(
      <svg>
        <ChartAxisLines layout={layout} zeroValueBaseline />
        <ChartSeriesBar layout={layout} points={points} seriesColor="#0a98d1" />
      </svg>,
    );
    const yAxis = container.querySelector('line[data-axis="y"]');
    expect(numericAttr(yAxis!, "x1")).toBeCloseTo(zero);
    const bars = container.querySelectorAll("rect.delpi-ui-series-chart__series-bar");
    expect(numericAttr(bars[0]!, "x") + numericAttr(bars[0]!, "width")).toBeCloseTo(zero);
    expect(numericAttr(bars[1]!, "x")).toBeCloseTo(zero);
  });

  it("mantém área clicável mínima sem desenhar perda do lado positivo", () => {
    const toY = (v: number) => 50 - v / 10;
    const negative = resolveZeroBasedValueSpan(toY, -1);
    const positive = resolveZeroBasedValueSpan(toY, 1);
    expect(ensureSelectableBarSpan(negative, -1, 4)).toEqual({ start: 50, size: 4 });
    expect(ensureSelectableBarSpan(positive, 1, 4)).toEqual({ start: 46, size: 4 });
    expect(ensureSelectableBarSpan(negative, -1, 0).size).toBeCloseTo(0.1);
  });
});
