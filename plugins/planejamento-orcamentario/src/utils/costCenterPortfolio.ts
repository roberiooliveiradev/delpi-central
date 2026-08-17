import type { BudgetResponsibility } from "../types/budgetPlanning";
import {
  fetchMyBudgetResponsibilities,
} from "../api/budgetPlanningApi";

export type CostCenterPortfolioItem = {
  key: string;
  unit_id: string;
  cost_center_id: string;
  cost_center_name: string | null;
  icon_key: string | null;
  area_id: string | null;
  branch: string | null;
  exercise_id: string;
  responsibility_type: string;
  user_name_snapshot?: string | null;
  user_email_snapshot?: string | null;
  canCapex: boolean;
  canPersonnel: boolean;
  capexResponsibility: BudgetResponsibility | null;
  personnelResponsibility: BudgetResponsibility | null;
};

function pairKey(unitId: string, costCenterId: string): string {
  return `${unitId}::${costCenterId}`;
}

export function mergeCostCenterPortfolio(
  capexItems: BudgetResponsibility[],
  personnelItems: BudgetResponsibility[],
): CostCenterPortfolioItem[] {
  const map = new Map<string, CostCenterPortfolioItem>();

  const upsert = (row: BudgetResponsibility, module: "capex" | "personnel") => {
    const unit_id = String(row.unit_id || "");
    const cost_center_id = String(row.cost_center_id || "");
    if (!unit_id || !cost_center_id) return;
    const key = pairKey(unit_id, cost_center_id);
    const current = map.get(key) ?? {
      key,
      unit_id,
      cost_center_id,
      cost_center_name: null,
      icon_key: null,
      area_id: row.area_id ?? null,
      branch: row.branch ?? row.unit_id ?? null,
      exercise_id: row.exercise_id,
      responsibility_type: row.responsibility_type,
      user_name_snapshot: row.user_name_snapshot,
      user_email_snapshot: row.user_email_snapshot,
      canCapex: false,
      canPersonnel: false,
      capexResponsibility: null,
      personnelResponsibility: null,
    };
    if (module === "capex") {
      current.canCapex = true;
      current.capexResponsibility = row;
    } else {
      current.canPersonnel = true;
      current.personnelResponsibility = row;
    }
    const name = String(row.cost_center_name || "").trim();
    if (name) current.cost_center_name = name;
    const icon = String(row.cost_center_icon_key || "").trim();
    if (icon) current.icon_key = icon;
    current.area_id = current.area_id ?? row.area_id ?? null;
    current.branch = current.branch ?? row.branch ?? row.unit_id ?? null;
    current.responsibility_type = row.responsibility_type || current.responsibility_type;
    map.set(key, current);
  };

  for (const row of capexItems) upsert(row, "capex");
  for (const row of personnelItems) upsert(row, "personnel");

  return Array.from(map.values()).sort((a, b) => {
    const byUnit = a.unit_id.localeCompare(b.unit_id);
    if (byUnit !== 0) return byUnit;
    const an = (a.cost_center_name || a.cost_center_id).localeCompare(
      b.cost_center_name || b.cost_center_id,
    );
    return an;
  });
}

export async function fetchMyCostCenterPortfolio(
  exerciseId: string,
  signal?: AbortSignal,
): Promise<CostCenterPortfolioItem[]> {
  const [capex, personnel] = await Promise.all([
    fetchMyBudgetResponsibilities("capex", exerciseId, signal),
    fetchMyBudgetResponsibilities("personnel", exerciseId, signal),
  ]);
  return mergeCostCenterPortfolio(capex.items ?? [], personnel.items ?? []);
}
