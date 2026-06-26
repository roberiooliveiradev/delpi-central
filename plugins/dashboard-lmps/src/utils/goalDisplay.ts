import { formatGoalScopeUnitLabel } from "./operationalUnitLabels";

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
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number | null;
};

function normalizeDecimals(value: number | null | undefined): number {
  const numeric = Number(value ?? 2);
  if (!Number.isFinite(numeric)) return 2;
  return Math.min(Math.max(Math.trunc(numeric), 0), 6);
}

function getSuffixSeparator(suffix: string): string {
  if (!suffix) return "";
  if (suffix === "%") return "";
  if (suffix.startsWith("/")) return "";
  return " ";
}

/** Formata valor/meta com prefixo, sufixo e decimais do catálogo SI (strategic indicators). */
export function formatDashboardMetricValue(
  value: number | null | undefined,
  fields?: DashboardGoalFields | null,
  options?: { fallback?: string },
): string {
  if (value == null || Number.isNaN(Number(value))) {
    return options?.fallback ?? "—";
  }

  const numeric = Number(value);
  const prefix = (fields?.value_prefix ?? "").trim();
  const suffix = (fields?.value_suffix ?? "").trim();
  const decimals = normalizeDecimals(fields?.value_decimals);

  const formattedNumber = numeric.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  const prefixText = prefix ? `${prefix} ` : "";
  const suffixText = suffix ? `${getSuffixSeparator(suffix)}${suffix}` : "";

  return `${prefixText}${formattedNumber}${suffixText}`;
}

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
  return formatGoalScopeUnitLabel(goalScopeBranch, scopeType);
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

  const comparable = goal.comparable_goal ?? goal.target ?? null;
  if (comparable != null) {
    const hasCatalogFormat =
      Boolean(goal.value_prefix?.trim()) ||
      Boolean(goal.value_suffix?.trim()) ||
      goal.value_decimals != null;

    if (hasCatalogFormat) {
      return formatDashboardMetricValue(comparable, goal);
    }

    if (formatComparable) {
      return formatComparable(comparable);
    }

    return formatDashboardMetricValue(comparable, goal);
  }

  if (goal.goal_label) {
    return goal.goal_label;
  }

  return null;
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
