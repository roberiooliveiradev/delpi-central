import { describe, expect, it } from "vitest";

import { buildRolPerUnitKpiView } from "./rolPerUnitPresentation";
import type { RolTargetData } from "../../types/analytics";

function money(value: number): string {
  return `R$ ${value}`;
}

describe("buildRolPerUnitKpiView consolidated goals", () => {
  it("exibe meta do payload consolidado SI (mesmo com scope_type per_unit)", () => {
    const consolidated: RolTargetData = {
      rol: 4_455_783.89,
      has_goal: true,
      goal_label: "Curva R$",
      goal_value: 4_690_000,
      comparable_goal: 4_690_000,
      reference_goal: 4_690_000,
      goal_scope_branch: "",
      goal_scope_label: "Meta consolidada",
      goal_scope_hint: null,
      scope_type: "per_unit",
      value_unit: "currency",
    };

    const view = buildRolPerUnitKpiView(
      { rol: 723_419, comparable_goal: 1_076_000, has_goal: true },
      { rol: 3_732_364, comparable_goal: 3_614_000, has_goal: true },
      "Consolidado",
      money,
      undefined,
      { consolidatedMetric: consolidated },
    );

    expect(view.value).toBe("R$ 4455783.89");
    expect(view.goalLabel).toBeTruthy();
    expect(view.goalScopeHint).toBeNull();
    expect(view.goalScopeBadge?.label ?? "").toMatch(/consolidada|unidade/i);
  });

  it("respeita goal_scope_hint do payload consolidado SI (sem inventar hint local)", () => {
    const consolidated: RolTargetData = {
      rol: 180_000,
      has_goal: false,
      comparable_goal: null,
      goal_scope_hint:
        "Metas cadastradas apenas por filial (01 e 02). Selecione uma filial no filtro.",
    };

    const view = buildRolPerUnitKpiView(
      { rol: 100_000, comparable_goal: 100_000, has_goal: true },
      { rol: 80_000, comparable_goal: 80_000, has_goal: true },
      "Consolidado",
      money,
      undefined,
      { consolidatedMetric: consolidated },
    );

    expect(view.goalLabel).toBeNull();
    expect(view.goalScopeHint ?? "").toMatch(/filial/i);
    expect(view.goalScopeHint ?? "").not.toMatch(/Santa Catarina/i);
  });

  it("sem payload consolidado não inventa «selecione unidade»", () => {
    const view = buildRolPerUnitKpiView(
      { rol: 100_000, comparable_goal: 100_000, has_goal: true },
      { rol: 80_000, comparable_goal: 80_000, has_goal: true },
      "Consolidado",
      money,
    );

    expect(view.value).toBe("R$ 180000");
    expect(view.goalLabel).toBeNull();
    expect(view.goalScopeHint).toBeNull();
  });
});
