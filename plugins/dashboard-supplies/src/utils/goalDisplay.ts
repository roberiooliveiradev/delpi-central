export type PerformanceDirection = "higher_is_better" | "lower_is_better";

export type GoalPerformanceTone = "success" | "warning";

export type GoalScopeBadgeTone = "scope" | "info";

export type GoalPerformanceBadge = {
  tone: GoalPerformanceTone;
  statusLabel: string;
  directionLabel: string;
};

export type GoalScopeBadge = {
  tone: GoalScopeBadgeTone;
  label: string;
};

export type DashboardGoalFields = {
  goal_label?: string | null;
  comparable_goal?: number | null;
  target?: number | null;
  has_goal?: boolean;
  goal_scope_branch?: string | null;
  goal_scope_label?: string | null;
  goal_scope_hint?: string | null;
  scope_type?: string | null;
  performance_direction?: PerformanceDirection | string | null;
  value_unit?: string | null;
  value_suffix?: string | null;
};

export type KpiGoalPresentation = {
  goalLabel: string | null;
  goalScopeBadge: GoalScopeBadge | null;
  goalScopeHint: string | null;
  goalPerformanceBadge: GoalPerformanceBadge | null;
  contextLabel: string;
};

export function formatGoalScopeLabel(
  goalScopeBranch?: string | null,
  scopeType?: string | null,
): string {
  const branch = (goalScopeBranch ?? "").trim();
  if (branch === "01" || branch === "02") {
    return `Meta filial ${branch}`;
  }
  if (branch) {
    return `Meta filial ${branch}`;
  }

  if ((scopeType ?? "").trim() === "per_unit") {
    return "Meta por unidade";
  }

  return "Meta consolidada";
}

export function resolveGoalScopeBadge(
  goal?: DashboardGoalFields | null,
): GoalScopeBadge | null {
  if (!goal) {
    return null;
  }

  const hint = goal.goal_scope_hint?.trim();
  if (hint) {
    return { tone: "info", label: hint };
  }

  const apiLabel = goal.goal_scope_label?.trim();
  if (apiLabel) {
    return { tone: "scope", label: apiLabel };
  }

  const goalLabel = goal.goal_label?.trim();
  const hasComparable =
    goal.comparable_goal != null && goal.comparable_goal > 0;

  if (!goalLabel && !hasComparable && goal.has_goal !== true) {
    return null;
  }

  return {
    tone: "scope",
    label: formatGoalScopeLabel(goal.goal_scope_branch, goal.scope_type),
  };
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

export function resolveOffTrackStatusLabel(
  direction?: PerformanceDirection | string | null,
): string {
  return direction === "lower_is_better" ? "Acima da meta" : "Abaixo da meta";
}

export function resolveGoalPerformanceBadge(
  realized: number | null | undefined,
  goal?: DashboardGoalFields | null,
): GoalPerformanceBadge | null {
  if (realized == null || !goal) {
    return null;
  }

  const comparable = goal.comparable_goal ?? goal.target;
  if (comparable == null || comparable <= 0) {
    return null;
  }

  const direction = goal.performance_direction ?? "higher_is_better";
  const directionLabel = formatPerformanceDirectionLabel(direction);
  if (!directionLabel) {
    return null;
  }

  const onTrack = isGoalOnTrack(realized, comparable, direction);

  return {
    tone: onTrack ? "success" : "warning",
    statusLabel: onTrack ? "Dentro da meta" : resolveOffTrackStatusLabel(direction),
    directionLabel,
  };
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
  const scopeBadge = showGoal ? resolveGoalScopeBadge(goal) : null;
  const goalLabel = showGoal ? resolveGoalLabel(goal, formatComparable) : null;
  const scopeHint =
    scopeBadge?.tone === "info" ? scopeBadge.label : goal?.goal_scope_hint?.trim() || null;

  return {
    goalLabel,
    goalScopeBadge: scopeBadge?.tone === "scope" ? scopeBadge : null,
    goalScopeHint: scopeHint,
    goalPerformanceBadge: showGoal
      ? resolveGoalPerformanceBadge(options?.realizedValue, goal)
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
