import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import {
  buildSeriesChartLayout,
  resolveSeriesChartCategoryBarSlot,
} from "./seriesChart/layout";
import {
  compactFiniteSeriesChartPoints,
  isSeriesChartFiniteValue,
  normalizeSeriesChartPointsForKind,
  seriesChartCompactsNullPoints,
  splitFiniteSeriesChartSegments,
  usableSeriesChartPoints,
  type SeriesChartPoint,
} from "./seriesChartOptions";

/** Sequência OTD reproduzível (null no início + fim de semana ausente). */
const OTD_POINTS: SeriesChartPoint[] = [
  { label: "02/11/26", value: null },
  { label: "03/11/26", value: 100 },
  { label: "04/11/26", value: 100 },
  { label: "05/11/26", value: 84 },
  { label: "06/11/26", value: 90.48 },
  { label: "09/11/26", value: 90.63 },
  { label: "10/11/26", value: 96.97 },
  { label: "11/11/26", value: 95.24 },
];

function axisLabels(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll(".delpi-ui-series-chart__tick--x")).map(
    (node) => (node.textContent ?? "").trim(),
  );
}

function barCenters(container: HTMLElement): number[] {
  return Array.from(container.querySelectorAll(".delpi-ui-series-chart__series-bar")).map((node) => {
    const x = Number(node.getAttribute("x"));
    const width = Number(node.getAttribute("width"));
    return x + width / 2;
  });
}

function lineAnchorXs(container: HTMLElement): number[] {
  const polylines = Array.from(
    container.querySelectorAll("polyline.delpi-ui-series-chart__series-line"),
  );
  const xs: number[] = [];
  for (const line of polylines) {
    const points = line.getAttribute("points") ?? "";
    for (const pair of points.trim().split(/\s+/).filter(Boolean)) {
      const x = Number(pair.split(",")[0]);
      if (Number.isFinite(x)) xs.push(x);
    }
  }
  return xs;
}

describe("series chart null alignment — shared pipeline", () => {
  it("não trata Number(null) como valor finito", () => {
    expect(isSeriesChartFiniteValue(null)).toBe(false);
    expect(isSeriesChartFiniteValue(undefined)).toBe(false);
    expect(isSeriesChartFiniteValue("")).toBe(false);
    expect(isSeriesChartFiniteValue(0)).toBe(true);
    expect(isSeriesChartFiniteValue(100)).toBe(true);
  });

  it("preserva categorias e reindexa densamente sem mutar a origem", () => {
    const original = OTD_POINTS.map((point) => ({ ...point }));
    const frozen = JSON.stringify(original);
    const normalized = usableSeriesChartPoints(original);

    expect(JSON.stringify(original)).toBe(frozen);
    expect(normalized).toHaveLength(8);
    expect(normalized.map((point) => point.label)).toEqual(OTD_POINTS.map((point) => point.label));
    expect(normalized.map((point) => point.value)).toEqual(OTD_POINTS.map((point) => point.value));
    expect(normalized.map((point) => point.sourceIndex)).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
  });

  it("null no início / meio / fim / múltiplos / sem null", () => {
    expect(
      usableSeriesChartPoints([
        { label: "a", value: null },
        { label: "b", value: 100 },
        { label: "c", value: 100 },
        { label: "d", value: 84 },
      ]).map((point) => [point.label, point.value, point.sourceIndex]),
    ).toEqual([
      ["a", null, 0],
      ["b", 100, 1],
      ["c", 100, 2],
      ["d", 84, 3],
    ]);

    expect(
      usableSeriesChartPoints([
        { label: "a", value: 100 },
        { label: "b", value: null },
        { label: "c", value: 84 },
      ]).map((point) => [point.label, point.value, point.sourceIndex]),
    ).toEqual([
      ["a", 100, 0],
      ["b", null, 1],
      ["c", 84, 2],
    ]);

    expect(
      usableSeriesChartPoints([
        { label: "a", value: 100 },
        { label: "b", value: 84 },
        { label: "c", value: null },
      ]).map((point) => [point.label, point.value, point.sourceIndex]),
    ).toEqual([
      ["a", 100, 0],
      ["b", 84, 1],
      ["c", null, 2],
    ]);

    expect(
      usableSeriesChartPoints([
        { label: "a", value: null },
        { label: "b", value: 10 },
        { label: "c", value: null },
        { label: "d", value: 20 },
        { label: "e", value: null },
      ]).map((point) => point.sourceIndex),
    ).toEqual([0, 1, 2, 3, 4]);

    expect(
      usableSeriesChartPoints([
        { label: "a", value: 1 },
        { label: "b", value: 2 },
      ]).map((point) => point.value),
    ).toEqual([1, 2]);
  });

  it("segmenta lacunas para linha/área sem deslocar índices", () => {
    const points = usableSeriesChartPoints([
      { label: "a", value: null },
      { label: "b", value: 100 },
      { label: "c", value: null },
      { label: "d", value: 84 },
      { label: "e", value: 90 },
    ]);
    expect(splitFiniteSeriesChartSegments(points).map((segment) => segment.map((p) => p.label))).toEqual([
      ["b"],
      ["d", "e"],
    ]);
  });

  it("pizza/funil compactam o ponto inteiro; linha/barra preservam lacuna", () => {
    expect(seriesChartCompactsNullPoints("pie")).toBe(true);
    expect(seriesChartCompactsNullPoints("bar")).toBe(false);
    expect(seriesChartCompactsNullPoints("line")).toBe(false);
    expect(seriesChartCompactsNullPoints("area")).toBe(false);

    const compacted = compactFiniteSeriesChartPoints(OTD_POINTS);
    expect(compacted).toHaveLength(7);
    expect(compacted[0]).toMatchObject({ label: "03/11/26", value: 100, sourceIndex: 0 });
    expect(normalizeSeriesChartPointsForKind("line", OTD_POINTS)).toHaveLength(8);
    expect(normalizeSeriesChartPointsForKind("pie", OTD_POINTS)).toHaveLength(7);
  });

  it("OTD: barra alinha cada label ao valor sem compactar o eixo", () => {
    const normalized = usableSeriesChartPoints(OTD_POINTS);
    expect(normalized.map((point) => point.label)).toEqual([
      "02/11/26",
      "03/11/26",
      "04/11/26",
      "05/11/26",
      "06/11/26",
      "09/11/26",
      "10/11/26",
      "11/11/26",
    ]);
    const layout = buildSeriesChartLayout({
      points: normalized,
      chartType: "bar",
    });
    const slot0 = resolveSeriesChartCategoryBarSlot({
      layout,
      categoryIndex: 0,
      categoryCount: normalized.length,
    }).centerX;
    const slot1 = resolveSeriesChartCategoryBarSlot({
      layout,
      categoryIndex: 1,
      categoryCount: normalized.length,
    }).centerX;
    const finiteCenters = normalized
      .filter((point) => isSeriesChartFiniteValue(point.value))
      .map((point) =>
        resolveSeriesChartCategoryBarSlot({
          layout,
          categoryIndex: point.sourceIndex!,
          categoryCount: normalized.length,
        }).centerX,
      );
    expect(finiteCenters).toHaveLength(7);
    expect(new Set(finiteCenters).size).toBe(7);
    // 03/11 (sourceIndex 1) ≠ slot da categoria nula 02/11.
    expect(finiteCenters[0]).toBe(slot1);
    expect(finiteCenters[0]).not.toBe(slot0);

    const { container } = render(
      <ConfigurableSeriesChart
        chartType="bar"
        points={OTD_POINTS}
        options={{
          showLegend: false,
          legendPosition: "hidden",
          showTitle: false,
          showMarkers: false,
          categoryLabelFormat: "raw",
        }}
      />,
    );

    const labels = axisLabels(container);
    expect(labels[0]).toContain("02/11");
    expect(labels.at(-1)).toContain("11/11");
    const bars = container.querySelectorAll(".delpi-ui-series-chart__series-bar");
    expect(bars).toHaveLength(7);
    const centers = barCenters(container);
    expect(new Set(centers).size).toBe(7);
    expect(centers[0]).toBeLessThan(centers[1]!);
  });

  it("OTD: linha preserva ordenação e não desloca 03/11", () => {
    const normalized = usableSeriesChartPoints(OTD_POINTS);
    const layout = buildSeriesChartLayout({
      points: normalized,
      chartType: "line",
    });
    const x0 = layout.toX(0, normalized.length);
    const x1 = layout.toX(1, normalized.length);
    expect(x1).toBeGreaterThan(x0);
    // Índice denso da coleção preservada: 03/11 = 1, não 0 após compactar.
    expect(
      normalized
        .filter((point) => isSeriesChartFiniteValue(point.value))
        .map((point) => point.sourceIndex),
    ).toEqual([1, 2, 3, 4, 5, 6, 7]);

    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={OTD_POINTS}
        options={{
          showLegend: false,
          legendPosition: "hidden",
          showTitle: false,
          showMarkers: true,
          categoryLabelFormat: "raw",
        }}
      />,
    );

    expect(axisLabels(container)[0]).toContain("02/11");
    const markers = Array.from(container.querySelectorAll(".delpi-ui-series-chart__series-marker"));
    expect(markers).toHaveLength(7);
    const markerXs = markers.map((node) => Number(node.getAttribute("cx")));
    expect(markerXs).toEqual([...markerXs].sort((a, b) => a - b));
    expect(new Set(markerXs).size).toBe(7);

    const ticks = Array.from(container.querySelectorAll(".delpi-ui-series-chart__tick--x"));
    const tick02 = ticks.find((node) => (node.textContent ?? "").includes("02/11"));
    expect(tick02).toBeTruthy();
    const tick02X = Number(tick02!.getAttribute("x"));
    // Valor 100 de 03/11 fica à direita da categoria nula 02/11 — sem colapsar no 1º slot.
    expect(markerXs[0]!).toBeGreaterThan(tick02X);

    const lineXs = lineAnchorXs(container);
    expect(lineXs.length).toBeGreaterThanOrEqual(7);
  });

  it("área e multi-série compartilham o mesmo eixo categórico", () => {
    const shared = [
      { label: "02/11/26", value: null as number | null },
      { label: "03/11/26", value: 100 },
      { label: "04/11/26", value: 50 },
    ];
    const { container: areaContainer } = render(
      <ConfigurableSeriesChart
        chartType="area"
        points={shared}
        options={{ showLegend: false, legendPosition: "hidden", showTitle: false }}
      />,
    );
    expect(axisLabels(areaContainer)).toHaveLength(3);
    expect(areaContainer.querySelector(".delpi-ui-series-chart__series-area")).toBeTruthy();

    const { container } = render(
      <ConfigurableSeriesChart
        chartType="line"
        points={shared}
        seriesList={[
          { name: "OTD", points: shared },
          {
            name: "Meta",
            points: [
              { label: "02/11/26", value: null },
              { label: "03/11/26", value: 95 },
              { label: "04/11/26", value: 95 },
            ],
          },
        ]}
        options={{ showLegend: true, legendPosition: "bottom", showTitle: false, showMarkers: true }}
      />,
    );
    expect(axisLabels(container)).toHaveLength(3);
    expect(container.querySelectorAll(".delpi-ui-series-chart__series-marker").length).toBe(4);
  });
});
