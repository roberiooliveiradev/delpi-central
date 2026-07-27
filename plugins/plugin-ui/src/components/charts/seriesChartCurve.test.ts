import { describe, expect, it } from "vitest";

import {
  densifySeriesChartCurve,
  resolveSeriesChartStrokePoints,
  seriesChartPointsAttr,
} from "./seriesChartCurve";

describe("seriesChartCurve", () => {
  const anchors = [
    { x: 0, y: 10 },
    { x: 10, y: 0 },
    { x: 20, y: 10 },
    { x: 30, y: 5 },
  ];

  it("densifica Catmull-Rom com mais pontos que os âncoras", () => {
    const dense = densifySeriesChartCurve(anchors, 8);
    expect(dense.length).toBeGreaterThan(anchors.length);
    expect(dense[0]).toEqual(anchors[0]);
    expect(dense[dense.length - 1]).toEqual(anchors[anchors.length - 1]);
  });

  it("sem smooth devolve só os âncoras", () => {
    const resolved = resolveSeriesChartStrokePoints(anchors, false);
    expect(resolved).toEqual(anchors);
    expect(seriesChartPointsAttr(resolved)).toBe("0,10 10,0 20,10 30,5");
  });

  it("com 2 pontos não densifica", () => {
    const pair = [
      { x: 0, y: 0 },
      { x: 5, y: 5 },
    ];
    expect(resolveSeriesChartStrokePoints(pair, true)).toEqual(pair);
  });
});
