export type DashboardGoalFields = {
  goal_label?: string | null;
  comparable_goal?: number | null;
  target?: number | null;
  has_goal?: boolean;
  value_unit?: string | null;
  value_suffix?: string | null;
};

export type KpiGoalPresentation = {
  goalLabel: string | null;
  contextLabel: string;
};

export function resolveGoalLabel(
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
): string | null {
  if (!goal) {
    return null;
  }

  if (goal.goal_label) {
    return goal.goal_label;
  }

  if (goal.comparable_goal == null) {
    return null;
  }

  if (formatComparable) {
    return formatComparable(goal.comparable_goal);
  }

  const suffix = goal.value_suffix?.trim();
  if (suffix) {
    return `${goal.comparable_goal} ${suffix}`;
  }

  return String(goal.comparable_goal);
}

export function buildKpiGoalPresentation(
  contextLabel: string,
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
  options?: { showGoal?: boolean },
): KpiGoalPresentation {
  const showGoal = options?.showGoal ?? true;
  return {
    goalLabel: showGoal ? resolveGoalLabel(goal, formatComparable) : null,
    contextLabel,
  };
}

/** @deprecated Prefer buildKpiGoalPresentation + KpiCard goalLabel */
export function formatGoalSubtitle(
  periodLabel: string,
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
): string {
  const { goalLabel, contextLabel } = buildKpiGoalPresentation(
    periodLabel,
    goal,
    formatComparable,
  );
  if (!goalLabel) {
    return contextLabel;
  }
  return `Meta: ${goalLabel} · ${contextLabel}`;
}
