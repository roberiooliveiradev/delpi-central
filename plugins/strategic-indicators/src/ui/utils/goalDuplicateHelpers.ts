import type { StrategicIndicatorGoalItem } from "../../data/types/indicatorGoals";

const DUPLICATE_LABEL_SUFFIX = " (cópia)";

export function buildDuplicateGoalLabel(goalLabel: string): string {
  const trimmed = goalLabel.trim();
  if (!trimmed) {
    return "Meta (cópia)";
  }
  if (trimmed.endsWith(DUPLICATE_LABEL_SUFFIX)) {
    return trimmed;
  }
  return `${trimmed}${DUPLICATE_LABEL_SUFFIX}`;
}

/** Valores iniciais do formulário ao duplicar uma meta existente (nova versão). */
export function buildGoalDuplicateSeed(
  source: StrategicIndicatorGoalItem,
): StrategicIndicatorGoalItem {
  return {
    ...source,
    id: "",
    goal_label: buildDuplicateGoalLabel(source.goal_label),
    version: 0,
    is_active: true,
    monthly_targets: source.monthly_targets.map((point) => ({ ...point })),
  };
}
