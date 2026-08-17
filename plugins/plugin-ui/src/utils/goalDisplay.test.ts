import { describe, expect, it } from "vitest";

import {
  buildKpiGoalPresentation,
  calculateIndicatorIddScore,
  isGoalOnTrack,
  resolveAccumulatedGoalPrefix,
  resolveGoalPeriodPartial,
} from "./goalDisplay";
import { formatGoalScopeUnitLabel, formatFilterViewScopeLabel } from "./operationalUnitLabels";

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
    expect(presentation.goalPrefix).toBe("Meta");
    expect(presentation.goalHint).toBeTruthy();
    expect(presentation.monthlyGoalLabel).toBeNull();
  });

  it("emite Meta mês e hints em período parcial", () => {
    const presentation = buildKpiGoalPresentation("ctx", {
      comparable_goal: 5,
      goal_value: 10,
      reference_goal: 10,
      goal_period_kind: "partial",
      goal_mode: "standard",
      value_suffix: "%",
      value_decimals: 1,
    });
    expect(presentation.goalPrefix).toBe("Meta parcial");
    expect(presentation.monthlyGoalPrefix).toBe("Meta mês");
    expect(presentation.monthlyGoalLabel).toContain("10");
    expect(presentation.goalHint).toMatch(/calculada/i);
    expect(presentation.monthlyGoalHint).toMatch(/cadastrado/i);
  });

  it("emite goalPrefix parcial / acumulada via kind", () => {
    expect(
      buildKpiGoalPresentation("ctx", {
        comparable_goal: 10,
        goal_period_kind: "partial",
      }).goalPrefix,
    ).toBe("Meta parcial");
    expect(
      buildKpiGoalPresentation("ctx", {
        comparable_goal: 10,
        goal_period_kind: "accumulated",
      }).goalPrefix,
    ).toBe("Meta acumulada");
    expect(
      buildKpiGoalPresentation(
        "ctx",
        { comparable_goal: 10 },
        undefined,
        { dateStart: "2026-01-01", dateEnd: "2026-08-15" },
      ).goalPrefix,
    ).toBe("Meta acumulada");
  });

  it("formata escopo consolidado por unidade", () => {
    expect(formatGoalScopeUnitLabel(null, "per_unit")).toBe("Meta por unidade");
    expect(formatGoalScopeUnitLabel("01", null)).toBe("Meta Santa Catarina");
    expect(formatFilterViewScopeLabel("consolidated", "")).toBe("Consolidado");
    expect(formatFilterViewScopeLabel("branch", "01")).toBe("Santa Catarina");
  });

  it("resolve prefixo Meta / parcial / acumulada via kind e flags", () => {
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 10,
        goal_period_kind: "exact",
      }),
    ).toBe("Meta");
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 10,
        goal_period_kind: "partial",
      }),
    ).toBe("Meta parcial");
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 10,
        goal_period_kind: "accumulated",
      }),
    ).toBe("Meta acumulada");
    // partial boolean true → parcial; false sem datas → Meta (mês fechado)
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 10,
        goal_period_partial: true,
      }),
    ).toBe("Meta parcial");
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 10,
        goal_period_partial: false,
      }),
    ).toBe("Meta");
  });

  it("deriva kind por start_date/end_date do goal (enrich api-delpi)", () => {
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 100,
        start_date: "2026-08-01",
        end_date: "2026-08-17",
      }),
    ).toBe("Meta parcial");
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 100,
        start_date: "2026-01-01",
        end_date: "2026-08-17",
      }),
    ).toBe("Meta acumulada");
    expect(
      resolveAccumulatedGoalPrefix({
        comparable_goal: 100,
        start_date: "2026-07-01",
        end_date: "2026-07-31",
      }),
    ).toBe("Meta");
  });
});
