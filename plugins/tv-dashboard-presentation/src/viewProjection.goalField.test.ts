import { describe, expect, it } from "vitest";

import {
  applyViewProjection,
  normalizeChartProjection,
  resolveProjectedGoalValue,
} from "./viewProjection";

describe("resolveProjectedGoalValue / goalField", () => {
  it("normaliza goalField e goalAggregation", () => {
    const next = normalizeChartProjection({
      series: [{ field: "otd" }],
      goalField: " meta ",
      goalAggregation: "avg",
    });
    expect(next?.goalField).toBe("meta");
    expect(next?.goalAggregation).toBe("avg");
  });

  it("agrega coluna constante", () => {
    const goal = resolveProjectedGoalValue(
      [{ meta: 95 }, { meta: 95 }, { meta: 95 }],
      "meta",
      "first",
    );
    expect(goal).toBe(95);
  });

  it("agrega avg", () => {
    const goal = resolveProjectedGoalValue([{ meta: 90 }, { meta: 100 }], "meta", "avg");
    expect(goal).toBe(95);
  });

  it("aplica projectedGoal no applyViewProjection", () => {
    const resolved = applyViewProjection(
      {
        table: {
          rows: [
            { otd: 98, meta: 95 },
            { otd: 97, meta: 95 },
          ],
          columns: [
            { key: "otd", label: "OTD" },
            { key: "meta", label: "Meta" },
          ],
        },
      },
      {
        chartProjection: {
          series: [{ field: "otd", aggregation: "first" }],
          goalField: "meta",
          goalAggregation: "first",
        },
        chartType: "line",
      },
    );
    expect(resolved?.chart?.projectedGoal).toBe(95);
  });
});
