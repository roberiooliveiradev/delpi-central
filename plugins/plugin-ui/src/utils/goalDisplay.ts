import { formatGoalScopeUnitLabel } from "./operationalUnitLabels";
import {
  resolveGoalLineHelp,
  type GoalLineHelpKind,
} from "./goalHelpContent";

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
  goal_value?: number | null;
  comparable_goal?: number | null;
  reference_goal?: number | null;
  target?: number | null;
  has_goal?: boolean;
  goal_aggregation?: string | null;
  goal_mode?: string | null;
  /** exact = one closed calendar month; partial = incomplete month; accumulated = multi-month. */
  goal_period_kind?: "exact" | "partial" | "accumulated" | string | null;
  goal_period_partial?: boolean | null;
  goal_scope_branch?: string | null;
  goal_scope_label?: string | null;
  goal_scope_hint?: string | null;
  scope_type?: string | null;
  performance_direction?: PerformanceDirection | string | null;
  value_unit?: string | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number | null;
  start_date?: string | null;
  end_date?: string | null;
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
  /** Prefixo Meta / Meta parcial / Meta acumulada; null se meta oculta. */
  goalPrefix: string | null;
  /** HelpTooltip da linha de meta do período. */
  goalHint: string | null;
  /** Segunda linha: Meta mês (reference_goal), só parcial/acumulado. */
  monthlyGoalLabel: string | null;
  monthlyGoalPrefix: string | null;
  monthlyGoalHint: string | null;
  goalScopeBadge: GoalScopeBadge | null;
  goalScopeHint: string | null;
  goalPerformanceBadge: GoalPerformanceBadge | null;
  iddScoreLabel: string | null;
  contextLabel: string;
};

/** Mesma regra do StrategicIndicatorsCalculator.calculate_indicator_score (SI). */
export function calculateIndicatorIddScore(
  realized: number | null | undefined,
  goal?: DashboardGoalFields | null,
): number | null {
  if (realized == null || Number.isNaN(Number(realized)) || !goal) {
    return null;
  }

  const comparable = goal.comparable_goal ?? goal.target;
  if (comparable == null || comparable <= 0) {
    return null;
  }

  const numericRealized = Number(realized);
  const numericGoal = Number(comparable);
  const lowerIsBetter = goal.performance_direction === "lower_is_better";

  if (lowerIsBetter) {
    if (numericRealized <= numericGoal) {
      return 10;
    }
    return Math.round(Math.min((numericGoal / numericRealized) * 10, 10) * 100) / 100;
  }

  if (numericRealized >= numericGoal) {
    return 10;
  }

  return Math.round(Math.min((numericRealized / numericGoal) * 10, 10) * 100) / 100;
}

export function formatIndicatorIddScore(
  score: number | null | undefined,
  fallback = "—",
): string {
  if (score == null || Number.isNaN(Number(score))) {
    return fallback;
  }

  return Number(score).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function resolveIddScoreLabel(
  realized: number | null | undefined,
  goal?: DashboardGoalFields | null,
): string | null {
  const score = calculateIndicatorIddScore(realized, goal);
  if (score == null) {
    return null;
  }

  return formatIndicatorIddScore(score);
}

export function resolveConsolidatedIddScoreLabel(
  entries: Array<{
    realized: number | null | undefined;
    goal?: DashboardGoalFields | null;
  }>,
): string | null {
  const scores = entries
    .map(({ realized, goal }) => calculateIndicatorIddScore(realized, goal))
    .filter((score): score is number => score != null);

  if (scores.length === 0) {
    return null;
  }

  const average =
    Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 100) /
    100;

  return formatIndicatorIddScore(average);
}

export type BranchMetricSlice<T extends DashboardGoalFields = DashboardGoalFields> =
  {
    realized: number | null | undefined;
    goal?: T | null;
  };

export type PerBranchMetricSlices<
  T extends DashboardGoalFields = DashboardGoalFields,
> = {
  filial01: BranchMetricSlice<T> | null;
  filial02: BranchMetricSlice<T> | null;
};

const OPERATIONAL_BRANCH_FILIALS = ["01", "02"] as const;

/** Injeta nota IDD consolidada (média 01+02) quando o filtro de unidade está aberto. */
export function applyConsolidatedBranchIddScore(
  presentation: KpiGoalPresentation,
  options: {
    activeBranch?: string;
    branches?: PerBranchMetricSlices | null;
  },
): KpiGoalPresentation {
  const branch = (options.activeBranch ?? "").trim();
  if (branch || !options.branches) {
    return presentation;
  }

  const { filial01, filial02 } = options.branches;
  const iddScoreLabel = resolveConsolidatedIddScoreLabel([
    { realized: filial01?.realized, goal: filial01?.goal },
    { realized: filial02?.realized, goal: filial02?.goal },
  ]);

  if (!iddScoreLabel) {
    return presentation;
  }

  return { ...presentation, iddScoreLabel };
}

export function buildKpiGoalPresentationWithBranchIdd<T extends DashboardGoalFields>(
  contextLabel: string,
  consolidatedGoal: T | null | undefined,
  options: {
    realizedValue?: number | null;
    activeBranch?: string;
    branches?: PerBranchMetricSlices<T> | null;
    formatComparable?: (value: number) => string;
    showGoal?: boolean;
    dateStart?: string | null;
    dateEnd?: string | null;
  },
): KpiGoalPresentation {
  const base = buildKpiGoalPresentation(
    contextLabel,
    consolidatedGoal,
    options.formatComparable,
    {
      showGoal: options.showGoal,
      realizedValue: options.realizedValue,
      dateStart: options.dateStart,
      dateEnd: options.dateEnd,
    },
  );

  return applyConsolidatedBranchIddScore(base, {
    activeBranch: options.activeBranch,
    branches: options.branches,
  });
}

/** Busca realizados e metas por filial 01/02 para cálculo IDD no consolidado. */
export async function fetchPerBranchMetricSlices<T extends DashboardGoalFields>(
  fetchMetric: (
    branch: (typeof OPERATIONAL_BRANCH_FILIALS)[number],
    signal?: AbortSignal,
  ) => Promise<T>,
  getRealized: (data: T) => number | null | undefined,
  signal?: AbortSignal,
  mapGoal?: (data: T) => DashboardGoalFields | null | undefined,
): Promise<PerBranchMetricSlices<T>> {
  const results = await Promise.allSettled(
    OPERATIONAL_BRANCH_FILIALS.map((branch) => fetchMetric(branch, signal)),
  );

  const data01 = results[0].status === "fulfilled" ? results[0].value : null;
  const data02 = results[1].status === "fulfilled" ? results[1].value : null;

  const toSlice = (data: T | null): BranchMetricSlice<T> | null => {
    if (!data) return null;
    const goal = (mapGoal?.(data) ?? data) as T;
    return { realized: getRealized(data), goal };
  };

  return {
    filial01: toSlice(data01),
    filial02: toSlice(data02),
  };
}

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

/**
 * Prefixo do KPI: «Meta» (1 mês fechado), «Meta parcial» (< 1 mês),
 * «Meta acumulada» (multi-mês). Prefer `goal_period_kind` da API.
 */
export function resolveAccumulatedGoalPrefix(
  goal?: DashboardGoalFields | null,
  options?: { dateStart?: string | null; dateEnd?: string | null },
): string {
  const kind = resolveGoalPeriodKind(goal, options);
  if (kind === "partial") return "Meta parcial";
  if (kind === "exact") return "Meta";
  return "Meta acumulada";
}

export function resolveGoalPeriodKind(
  goal?: DashboardGoalFields | null,
  options?: { dateStart?: string | null; dateEnd?: string | null },
): "exact" | "partial" | "accumulated" {
  const raw = (goal?.goal_period_kind ?? "").toString().trim().toLowerCase();
  if (raw === "exact" || raw === "partial" || raw === "accumulated") {
    return raw;
  }

  if (typeof goal?.goal_period_partial === "boolean" && goal.goal_period_partial) {
    return "partial";
  }

  const start = (goal?.start_date ?? options?.dateStart ?? "").trim();
  const end = (goal?.end_date ?? options?.dateEnd ?? "").trim();
  if (!start || !end) {
    // Sem datas: partial explícito manda; caso contrário Meta (não acumulada).
    if (goal?.goal_period_partial === true) {
      return "partial";
    }
    return "exact";
  }

  return resolveCalendarPeriodKind(start, end);
}

export function resolveGoalPeriodPartial(
  goal?: DashboardGoalFields | null,
  options?: { dateStart?: string | null; dateEnd?: string | null },
): boolean {
  return resolveGoalPeriodKind(goal, options) === "partial";
}

function parseFlexibleDateParts(value: string): { y: number; m: number; d: number } | null {
  const iso = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) {
    return { y: Number(iso[1]), m: Number(iso[2]), d: Number(iso[3]) };
  }
  const br = value.match(/^(\d{2})[-/](\d{2})[-/](\d{4})/);
  if (br) {
    return { y: Number(br[3]), m: Number(br[2]), d: Number(br[1]) };
  }
  return null;
}

function daysInMonth(y: number, m: number): number {
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

/** Alinhado ao SI: exact / partial / accumulated por overlap de meses civis. */
function resolveCalendarPeriodKind(
  start: string,
  end: string,
): "exact" | "partial" | "accumulated" {
  const a = parseFlexibleDateParts(start);
  const b = parseFlexibleDateParts(end);
  if (!a || !b) {
    return "accumulated";
  }

  if (a.y !== b.y || a.m !== b.m) {
    return "accumulated";
  }

  const dim = daysInMonth(a.y, a.m);
  if (a.d === 1 && b.d === dim) {
    return "exact";
  }
  return "partial";
}

export function buildKpiGoalPresentation(
  contextLabel: string,
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
  options?: {
    showGoal?: boolean;
    realizedValue?: number | null;
    dateStart?: string | null;
    dateEnd?: string | null;
  },
): KpiGoalPresentation {
  const showGoal = options?.showGoal ?? true;
  const scopeBadge = showGoal ? resolveGoalScopeBadge(goal) : null;
  const goalLabel = showGoal ? resolveGoalLabel(goal, formatComparable) : null;
  const scopeHint =
    scopeBadge?.tone === "info" ? scopeBadge.label : goal?.goal_scope_hint?.trim() || null;
  const dateOpts = {
    dateStart: options?.dateStart,
    dateEnd: options?.dateEnd,
  };
  const kind = resolveGoalPeriodKind(goal, dateOpts) as GoalLineHelpKind;
  const goalPrefix =
    showGoal && goalLabel
      ? resolveAccumulatedGoalPrefix(goal, dateOpts)
      : null;
  const goalHint =
    showGoal && goalLabel
      ? resolveGoalLineHelp({ kind, goalMode: goal?.goal_mode, line: "period" })
      : null;

  const showMonthlyLine =
    showGoal && (kind === "partial" || kind === "accumulated");
  const monthlyRaw =
    goal?.reference_goal ?? goal?.goal_value ?? null;
  const monthlyGoalLabel =
    showMonthlyLine && monthlyRaw != null && !Number.isNaN(Number(monthlyRaw))
      ? formatComparable
        ? formatComparable(Number(monthlyRaw))
        : formatDashboardMetricValue(Number(monthlyRaw), goal)
      : null;
  const monthlyGoalPrefix = monthlyGoalLabel ? "Meta mês" : null;
  const monthlyGoalHint =
    monthlyGoalLabel != null
      ? resolveGoalLineHelp({
          kind,
          goalMode: goal?.goal_mode,
          line: "monthly",
        })
      : null;

  return {
    goalLabel,
    goalPrefix,
    goalHint,
    monthlyGoalLabel,
    monthlyGoalPrefix,
    monthlyGoalHint,
    goalScopeBadge: scopeBadge?.tone === "scope" ? scopeBadge : null,
    goalScopeHint: scopeHint,
    goalPerformanceBadge: showGoal
      ? resolveGoalPerformanceBadge(options?.realizedValue, goal)
      : null,
    iddScoreLabel: showGoal
      ? resolveIddScoreLabel(options?.realizedValue, goal)
      : null,
    contextLabel,
  };
}

/** Fragmentos de meta para export tabular (Meta do período + Meta mês). */
export function formatKpiGoalExportFragments(
  presentation: Pick<
    KpiGoalPresentation,
    "goalLabel" | "goalPrefix" | "monthlyGoalLabel" | "monthlyGoalPrefix"
  > | null | undefined,
): string[] {
  if (!presentation) {
    return [];
  }
  const parts: string[] = [];
  if (presentation.goalLabel) {
    const prefix = (presentation.goalPrefix ?? "Meta").trim();
    parts.push(`${prefix} ${presentation.goalLabel}`.trim());
  }
  if (presentation.monthlyGoalLabel) {
    const prefix = (presentation.monthlyGoalPrefix ?? "Meta mês").trim();
    parts.push(`${prefix} ${presentation.monthlyGoalLabel}`.trim());
  }
  return parts;
}

/** Junta contexto base + fragmentos de meta para coluna `contexto` do export. */
export function joinKpiExportContext(
  ...parts: Array<string | null | undefined>
): string {
  return parts
    .map((part) => (part ?? "").trim())
    .filter(Boolean)
    .join(" · ");
}

/** @deprecated Prefer buildKpiGoalPresentation + KpiCard goalLabel */
export function formatGoalSubtitle(
  periodLabel: string,
  goal?: DashboardGoalFields | null,
  formatComparable?: (value: number) => string,
  realizedValue?: number | null,
): string {
  const { goalLabel, iddScoreLabel, contextLabel } = buildKpiGoalPresentation(
    periodLabel,
    goal,
    formatComparable,
    { realizedValue },
  );
  const parts: string[] = [];
  if (goalLabel) {
    parts.push(`Meta: ${goalLabel}`);
  }
  if (iddScoreLabel) {
    parts.push(`Nota IDD: ${iddScoreLabel}`);
  }
  if (parts.length === 0) {
    return contextLabel;
  }
  return `${parts.join(" · ")} · ${contextLabel}`;
}
