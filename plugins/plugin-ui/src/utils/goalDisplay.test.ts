import { describe, expect, it } from "vitest";

import {
  buildKpiGoalPresentation,
  buildKpiGoalPresentationWithBranchIdd,
  buildSiIndicatorScoreMap,
  calculateIndicatorIddScore,
  formatKpiGoalExportFragments,
  isGoalOnTrack,
  joinKpiExportContext,
  pickSiIddScoreLabel,
  resolveAccumulatedGoalPrefix,
  resolveAverageSiIddScoreLabel,
  resolveGoalPeriodPartial,
  resolveIndicatorIddScoreLabelFromSi,
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

  it("formata score SI sem recalcular no MFE", () => {
    expect(resolveIndicatorIddScoreLabelFromSi(6.57)).toBe("6,57");
    expect(resolveIndicatorIddScoreLabelFromSi(null)).toBeNull();
    const map = buildSiIndicatorScoreMap([
      { indicator_id: "quality-kaizen-financial", score: 6.57 },
    ]);
    expect(pickSiIddScoreLabel(map, "quality-kaizen-financial")).toBe("6,57");
    expect(resolveAverageSiIddScoreLabel([8, 6])).toBe("7,00");
  });

  it("respeita iddScoreLabel do SI em buildKpiGoalPresentationWithBranchIdd", () => {
    const presentation = buildKpiGoalPresentationWithBranchIdd(
      "ctx",
      {
        comparable_goal: 9000,
        performance_direction: "higher_is_better",
      },
      {
        realizedValue: 4098,
        iddScoreLabel: resolveIndicatorIddScoreLabelFromSi(6.57),
      },
    );
    expect(presentation.iddScoreLabel).toBe("6,57");
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

  it("não exibe Meta R$ 0,00 nem IDD quando SI não tem meta", () => {
    const presentation = buildKpiGoalPresentation(
      "ctx",
      {
        comparable_goal: 0,
        target: 0,
        performance_direction: "higher_is_better",
        value_prefix: "R$",
      },
      undefined,
      { realizedValue: 100, showGoal: true },
    );
    expect(presentation.goalLabel).toBeNull();
    expect(presentation.goalPrefix).toBeNull();
    expect(presentation.goalPerformanceBadge).toBeNull();
    expect(presentation.iddScoreLabel).toBeNull();
  });

  it("não usa o nome do indicador como Meta parcial quando a meta SI é zero", () => {
    const presentation = buildKpiGoalPresentation(
      "ctx",
      {
        comparable_goal: 0,
        target: 0,
        goal_label: "ROL Novos Negócios",
        goal_period_kind: "partial",
        value_prefix: "R$",
        value_decimals: 2,
      },
      undefined,
      { realizedValue: 137551.78, showGoal: true },
    );
    expect(presentation.goalLabel).toBeNull();
    expect(presentation.goalPrefix).toBeNull();
    expect(presentation.monthlyGoalLabel).toBeNull();
  });

  it("mantém goal_label só quando não há valor numérico de meta", () => {
    const presentation = buildKpiGoalPresentation("ctx", {
      comparable_goal: null,
      target: null,
      goal_label: "≥ 95%",
    });
    expect(presentation.goalLabel).toBe("≥ 95%");
  });

  it("omite Meta mês quando reference_goal é zero", () => {
    const presentation = buildKpiGoalPresentation("ctx", {
      comparable_goal: 5,
      goal_value: 0,
      reference_goal: 0,
      goal_period_kind: "partial",
      value_suffix: "%",
      value_decimals: 1,
    });
    expect(presentation.goalLabel).toContain("5");
    expect(presentation.monthlyGoalLabel).toBeNull();
  });

  it("omite meta numérica quando há goal_scope_hint (selecione unidade)", () => {
    const presentation = buildKpiGoalPresentation("ctx", {
      comparable_goal: 1_076_000,
      reference_goal: 1_076_000,
      goal_value: 1_076_000,
      goal_period_kind: "partial",
      goal_scope_hint:
        "Metas cadastradas apenas por unidade. Selecione uma unidade no filtro.",
      value_prefix: "R$",
      value_decimals: 2,
    });
    expect(presentation.goalLabel).toBeNull();
    expect(presentation.monthlyGoalLabel).toBeNull();
    expect(presentation.goalScopeHint).toMatch(/Selecione uma unidade/i);
    expect(formatKpiGoalExportFragments(presentation)).toEqual([]);
  });

  it("formata fragmentos de export com Meta mês", () => {
    const presentation = buildKpiGoalPresentation("ctx", {
      comparable_goal: 5,
      goal_value: 10,
      reference_goal: 10,
      goal_period_kind: "partial",
      value_suffix: "%",
      value_decimals: 1,
    });
    const fragments = formatKpiGoalExportFragments(presentation);
    expect(fragments.some((part) => part.startsWith("Meta parcial"))).toBe(true);
    expect(fragments.some((part) => part.startsWith("Meta mês"))).toBe(true);
    expect(joinKpiExportContext("SC", ...fragments)).toContain("Meta mês");
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
