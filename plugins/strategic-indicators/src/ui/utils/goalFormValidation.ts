import type { GoalScopeBranch } from "../../data/types/indicatorGoals";
import type { ScopeType } from "../../data/types/settings";
import { clampGoalYear, MIN_GOAL_YEAR, MAX_GOAL_YEAR } from "./goalYearHelpers";

const VALID_SCOPE_BRANCHES = new Set<GoalScopeBranch | "">(["", "01", "02"]);

export type IndicatorGoalCatalogEntry = {
  indicatorId: string;
  scopeType?: ScopeType;
};

export function validateIndicatorGoalForm(input: {
  indicatorId: string;
  goalYear: number;
  goalLabel: string;
  goalScopeBranch: string;
  goalMode: "standard" | "monthly_curve";
  goalValue: number;
  monthlyTargets: Array<{ target_value: number }>;
  indicatorOptions?: Array<{ value: string }>;
  indicatorCatalog?: IndicatorGoalCatalogEntry[];
  isEditing: boolean;
}): string | null {
  const label = input.goalLabel.trim();
  if (!label) {
    return "O nome da meta é obrigatório.";
  }

  if (!input.isEditing && !input.indicatorId.trim()) {
    return "Selecione um indicador.";
  }

  if (input.indicatorOptions?.length) {
    const allowed = new Set(input.indicatorOptions.map((option) => option.value));
    if (input.indicatorId.trim() && !allowed.has(input.indicatorId.trim())) {
      return "Indicador inválido ou inativo no catálogo.";
    }
  }

  const year = clampGoalYear(Number(input.goalYear));
  if (year < MIN_GOAL_YEAR || year > MAX_GOAL_YEAR) {
    return `O ano da meta deve estar entre ${MIN_GOAL_YEAR} e ${MAX_GOAL_YEAR}.`;
  }

  const scope = (input.goalScopeBranch ?? "").trim();
  if (!VALID_SCOPE_BRANCHES.has(scope as GoalScopeBranch | "")) {
    return "Escopo inválido: use consolidado ou filial 01/02.";
  }

  if (input.goalMode === "standard" && input.goalValue < 0) {
    return "O valor da meta não pode ser negativo.";
  }

  if (input.goalMode === "monthly_curve") {
    const hasInvalidMonthlyValue = input.monthlyTargets.some(
      (item) => Number(item.target_value) < 0,
    );
    if (hasInvalidMonthlyValue) {
      return "Os valores mensais não podem ser negativos.";
    }
  }

  return null;
}
