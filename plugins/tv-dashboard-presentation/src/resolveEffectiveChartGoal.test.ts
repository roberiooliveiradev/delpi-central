import { describe, expect, it } from "vitest";

import { resolveEffectiveChartGoal } from "./resolveEffectiveChartGoal";

describe("resolveEffectiveChartGoal", () => {
  it("manual finito ganha sobre coluna projetada", () => {
    expect(
      resolveEffectiveChartGoal({ goalLineValue: 97, projectedGoal: 90 }),
    ).toBe(97);
  });

  it("usa projectedGoal quando override ausente", () => {
    expect(
      resolveEffectiveChartGoal({ goalLineValue: null, projectedGoal: 95 }),
    ).toBe(95);
  });

  it("retorna null sem valor efetivo", () => {
    expect(resolveEffectiveChartGoal({ goalLineValue: null, projectedGoal: null })).toBeNull();
    expect(resolveEffectiveChartGoal({ goalLineValue: Number.NaN, projectedGoal: undefined })).toBeNull();
  });
});
