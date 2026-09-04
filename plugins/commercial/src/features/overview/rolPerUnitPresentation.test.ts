import { describe, expect, it } from "vitest";

import { buildRolPerUnitKpiView } from "./rolPerUnitPresentation";
import type { RolTargetData } from "../../types/analytics";

function money(value: number): string {
  return `R$ ${value}`;
}

describe("buildRolPerUnitKpiView consolidated goals", () => {
  it("exibe meta do payload consolidado SI sem hint de unidade", () => {
    const consolidated: RolTargetData = {
      rol: 180_000,
      has_goal: true,
      goal_label: "R$ 180.000,00",
      goal_value: 180_000,
      comparable_goal: 180_000,
      reference_goal: 180_000,
      goal_scope_branch: "",
      goal_scope_hint: null,
      value_unit: "currency",
    };

    const view = buildRolPerUnitKpiView(null, null, "Consolidado", money, undefined, {
      consolidatedMetric: consolidated,
    });

    expect(view.value).toBe("R$ 180000");
    expect(view.goalLabel).toBeTruthy();
    expect(view.goalScopeHint).toBeNull();
  });

  it("mantém hint quando não há payload consolidado com meta", () => {
    const view = buildRolPerUnitKpiView(
      { rol: 100_000, comparable_goal: 100_000, has_goal: true },
      { rol: 80_000, comparable_goal: 80_000, has_goal: true },
      "Consolidado",
      money,
    );

    expect(view.goalScopeHint ?? "").toMatch(/unidade|filial/i);
    expect(view.goalLabel).toBeNull();
  });
});
