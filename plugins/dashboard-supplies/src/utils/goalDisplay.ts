export type PerformanceDirection = "higher_is_better" | "lower_is_better";

export type DashboardGoalFields = {
  goal_label?: string | null;
  comparable_goal?: number | null;
  target?: number | null;
  has_goal?: boolean;
  goal_scope_branch?: string | null;
  scope_type?: string | null;
  performance_direction?: PerformanceDirection | string | null;
  value_unit?: string | null;
  value_suffix?: string | null;
};

export type KpiGoalPresentation = {
  goalLabel: string | null;
  goalScopeLabel: string | null;
  goalStatusLabel: string | null;
  contextLabel: string;
};

export function formatGoalScopeLabel(
  goalScopeBranch?: string | null,
  scopeType?: string | null,
): string | null {
  const branch = (goalScopeBranch ?? "").trim();
  if (branch) {
    return `Filial ${branch}`;
  }

  if ((scopeType ?? "").trim() === "per_unit") {
    return "Por unidade";
  }

  return "Consolidado";
}

export function formatPerformanceDirectionLabel(
  direction?: PerformanceDirection | string | null,
): string | null {
  switch (direction) {
    case "higher_is_better":
      return "Quanto maior, melhor";
    case "lower_is_better":
      return "Quanto menor, melhor";
    default:
      return null;
  }
}

export function isGoalOnTrack(
  realized: number,
  comparableGoal: number,
  direction?: PerformanceDirection | string | null,
): boolean {
  if (comparableGoal <= 0) {
    return true;
  }

  if (direction === "lower_is_better") {
    return realized <= comparableGoal;
  }

  return realized >= comparableGoal;
}

export function resolveGoalPerformanceStatusLabel(
  realized: number | null | undefined,
  goal?: DashboardGoalFields | null,
): string | null {
  if (realized == null || !goal) {
    return null;
  }

  const comparable = goal.comparable_goal ?? goal.target;
  if (comparable == null || comparable <= 0) {
    return null;
  }

  const direction = goal.performance_direction ?? "higher_is_better";
  if (isGoalOnTrack(realized, comparable, direction)) {
    return null;
  }

  const directionLabel = formatPerformanceDirectionLabel(direction);
  if (!directionLabel) {
    return null;
  }

  const statusLabel =
    direction === "lower_is_better" ? "Acima da meta" : "Abaixo da meta";
  return `${statusLabel} · ${directionLabel}`;
}

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
  options?: { showGoal?: boolean; realizedValue?: number | null },
): KpiGoalPresentation {
  const showGoal = options?.showGoal ?? true;
  const goalLabel = showGoal ? resolveGoalLabel(goal, formatComparable) : null;

  return {
    goalLabel,
    goalScopeLabel: showGoal && goalLabel ? formatGoalScopeLabel(
      goal?.goal_scope_branch,
      goal?.scope_type,
    ) : null,
    goalStatusLabel: showGoal
      ? resolveGoalPerformanceStatusLabel(options?.realizedValue, goal)
      : null,
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
