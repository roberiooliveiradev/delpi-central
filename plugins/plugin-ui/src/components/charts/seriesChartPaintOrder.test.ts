import { describe, expect, it } from "vitest";

import {
  orderSeriesIndicesForOverlappingPaint,
  seriesPaintMagnitude,
} from "./seriesChartPaintOrder";

describe("seriesChartPaintOrder", () => {
  it("magnitude média dos valores absolutos", () => {
    expect(
      seriesPaintMagnitude({
        points: [{ value: 100 }, { value: 300 }, { value: null }],
      }),
    ).toBe(200);
  });

  it("pinta a maior série atrás e a menor na frente", () => {
    const seriesList = [
      { points: [{ value: 800 }, { value: 800 }] }, // investimento
      { points: [{ value: 200 }, { value: 250 }] }, // economia
    ];
    expect(orderSeriesIndicesForOverlappingPaint(seriesList)).toEqual([0, 1]);
  });

  it("reordena quando a menor veio primeiro na lista", () => {
    const seriesList = [
      { points: [{ value: 50 }] },
      { points: [{ value: 900 }] },
      { points: [{ value: 200 }] },
    ];
    expect(orderSeriesIndicesForOverlappingPaint(seriesList)).toEqual([1, 2, 0]);
  });
});
