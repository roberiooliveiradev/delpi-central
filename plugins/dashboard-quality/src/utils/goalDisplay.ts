export type DashboardGoalFields = {
  goal_label?: string | null;
  comparable_goal?: number | null;
  target?: number | null;
  has_goal?: boolean;
};

export function formatGoalSubtitle(
  periodLabel: string,
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
): string {
  if (!goal) {
    return periodLabel;
  }

  const meta =
    goal.goal_label ??
    (goal.comparable_goal != null && formatComparable
      ? formatComparable(goal.comparable_goal)
      : goal.comparable_goal != null
        ? String(goal.comparable_goal)
        : null);

  if (!meta) {
    return periodLabel;
  }

  return `Meta: ${meta} · ${periodLabel}`;
}

export function formatGoalDescription(
  description: string,
  goal?: DashboardGoalFields | null,
): string {
  if (!goal?.goal_label) {
    return description;
  }
  return `Meta: ${goal.goal_label} · ${description}`;
}
