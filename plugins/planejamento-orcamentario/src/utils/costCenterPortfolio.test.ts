import { describe, expect, it } from "vitest";

import type { BudgetResponsibility } from "../types/budgetPlanning";
import { mergeCostCenterPortfolio } from "./costCenterPortfolio";

function resp(
  partial: Partial<BudgetResponsibility> & {
    unit_id: string;
    cost_center_id: string;
    module: string;
  },
): BudgetResponsibility {
  return {
    id: partial.id ?? `${partial.module}-${partial.cost_center_id}`,
    exercise_id: partial.exercise_id ?? "ex-1",
    module: partial.module,
    user_sub: partial.user_sub ?? "sub-1",
    unit_id: partial.unit_id,
    cost_center_id: partial.cost_center_id,
    cost_center_name: partial.cost_center_name ?? null,
    cost_center_icon_key: partial.cost_center_icon_key ?? null,
    area_id: partial.area_id ?? null,
    branch: partial.branch ?? partial.unit_id,
    responsibility_type: partial.responsibility_type ?? "owner",
    is_active: true,
  } as BudgetResponsibility;
}

describe("mergeCostCenterPortfolio", () => {
  it("une CAPEX e Pessoal do mesmo CC", () => {
    const merged = mergeCostCenterPortfolio(
      [
        resp({
          module: "capex",
          unit_id: "02",
          cost_center_id: "0205",
          cost_center_name: "Produção ES",
        }),
        resp({ module: "capex", unit_id: "02", cost_center_id: "0203" }),
      ],
      [resp({ module: "personnel", unit_id: "02", cost_center_id: "0205" })],
    );
    expect(merged).toHaveLength(2);
    const a = merged.find((i) => i.cost_center_id === "0205");
    expect(a?.canCapex).toBe(true);
    expect(a?.canPersonnel).toBe(true);
    expect(a?.cost_center_name).toBe("Produção ES");
    const b = merged.find((i) => i.cost_center_id === "0203");
    expect(b?.canCapex).toBe(true);
    expect(b?.canPersonnel).toBe(false);
  });
});
