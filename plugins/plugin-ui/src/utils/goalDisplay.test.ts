import { describe, expect, it } from "vitest";

import {
  buildKpiGoalPresentation,
  calculateIndicatorIddScore,
  isGoalOnTrack,
} from "./goalDisplay";
import { formatGoalScopeUnitLabel } from "./operationalUnitLabels";

describe("goalDisplay", () => {
  it("calcula nota IDD 10 quando realizado atinge meta (higher is better)", () => {
    const score = calculateIndicatorIddScore(95, {
      comparable_goal: 90,
      performance_direction: "higher_is_better",
    });
    expect(score).toBe(10);
  });

  it("identifica KPI fora da meta", () => {
    expect(
      isGoalOnTrack(80, 90, "higher_is_better"),
    ).toBe(false);
  });

  it("monta apresentação com meta e contexto", () => {
    const presentation = buildKpiGoalPresentation("Jan/2026", {
      comparable_goal: 90,
      performance_direction: "higher_is_better",
      value_suffix: "%",
      value_decimals: 1,
    }, undefined, { realizedValue: 95, showGoal: true });

    expect(presentation.goalLabel).toContain("90");
    expect(presentation.contextLabel).toBe("Jan/2026");
    expect(presentation.goalPerformanceBadge?.tone).toBe("success");
  });

  it("formata escopo consolidado por unidade", () => {
    expect(formatGoalScopeUnitLabel(null, "per_unit")).toBe("Meta por unidade");
    expect(formatGoalScopeUnitLabel("01", null)).toBe("Meta Santa Catarina");
  });
});
