import type { GoalMode, GoalPeriodicity } from "../../data/types/indicatorGoals";

export const MONTHLY_CURVE_POINT_COUNT = 12;

export function isMonthlyCurveMode(goalMode: GoalMode | string | null | undefined) {
  return goalMode === "monthly_curve";
}

/** Valor enviado à API: curvas mensais não persistem consolidado em goal_value. */
export function resolveGoalValueForApi(
  goalMode: GoalMode,
  goalValue: number,
): number {
  return isMonthlyCurveMode(goalMode) ? 0 : Number(goalValue || 0);
}

export function expectedMonthlyCurvePointCount(
  periodicity: GoalPeriodicity | string,
): number {
  switch (periodicity) {
    case "quarterly":
      return 4;
    case "weekly":
      return 52;
    case "annual":
      return 1;
    case "monthly":
    default:
      return MONTHLY_CURVE_POINT_COUNT;
  }
}

export function formatAdminGoalMeta(item: {
  goal_label: string;
  goal_value: number;
  goal_mode: GoalMode | string;
}): string {
  if (isMonthlyCurveMode(item.goal_mode)) {
    return item.goal_label;
  }
  return `${item.goal_label} · ${item.goal_value}`;
}

export function formatAdminGoalValueOnly(item: {
  goal_value: number;
  goal_mode: GoalMode | string;
}): string {
  if (isMonthlyCurveMode(item.goal_mode)) {
    return "Curva mensal";
  }
  return String(item.goal_value);
}
