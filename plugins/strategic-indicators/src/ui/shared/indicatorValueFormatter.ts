export const MISSING_VALUE_LABEL = "Sem dados preenchidos";

export function isMissingValueClassification(
  classification: string | null | undefined,
): boolean {
  return (classification ?? "").trim().toLowerCase() === MISSING_VALUE_LABEL.toLowerCase();
}

export function formatIndicatorScore(
  score: number | null | undefined,
  options: FormatIndicatorValueOptions = {},
): string {
  if (score === null || score === undefined) {
    return options.fallback ?? MISSING_VALUE_LABEL;
  }

  const numeric = Number(score);
  if (!Number.isFinite(numeric)) {
    return options.fallback ?? MISSING_VALUE_LABEL;
  }

  return numeric.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export type IndicatorValueFormat = {
  valueUnit?: string | null;
  valuePrefix?: string | null;
  valueSuffix?: string | null;
  valueDecimals?: number | null;

  value_unit?: string | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number | null;
};

type FormatIndicatorValueOptions = {
  signed?: boolean;
  fallback?: string;
  /** Substitui o rótulo "Consolidado" quando a visão do painel é por filial. */
  filterViewScopeLabel?: string;
  /** Filial ativa (01/02) para prefixar valores unitários. */
  activeBranch?: string;
};

function normalizeNumber(value: number | null | undefined): number | null {
  if (value === null || value === undefined) return null;

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;

  return numeric;
}

function normalizeDecimals(value: number | null | undefined): number {
  const numeric = Number(value ?? 2);

  if (!Number.isFinite(numeric)) return 2;

  return Math.min(Math.max(Math.trunc(numeric), 0), 6);
}

function resolvePrefix(format: IndicatorValueFormat): string {
  return (format.valuePrefix ?? format.value_prefix ?? "").trim();
}

function resolveSuffix(format: IndicatorValueFormat): string {
  return (format.valueSuffix ?? format.value_suffix ?? "").trim();
}

function resolveDecimals(format: IndicatorValueFormat): number {
  return normalizeDecimals(format.valueDecimals ?? format.value_decimals ?? 2);
}

function getSuffixSeparator(suffix: string): string {
  if (!suffix) return "";
  if (suffix === "%") return "";
  if (suffix.startsWith("/")) return "";
  return " ";
}

export function formatIndicatorValue(
  value: number | null | undefined,
  format: IndicatorValueFormat = {},
  options: FormatIndicatorValueOptions = {},
): string {
  const numeric = normalizeNumber(value);

  if (numeric === null) {
    return options.fallback ?? MISSING_VALUE_LABEL;
  }

  const prefix = resolvePrefix(format);
  const suffix = resolveSuffix(format);
  const decimals = resolveDecimals(format);

  const shouldShowExplicitSign = Boolean(options.signed) && numeric !== 0;
  const sign = shouldShowExplicitSign
    ? numeric > 0
      ? "+"
      : "-"
    : numeric < 0
      ? "-"
      : "";

  const absoluteValue =
    shouldShowExplicitSign || numeric < 0 ? Math.abs(numeric) : numeric;

  const formattedNumber = absoluteValue.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  const prefixText = prefix ? `${prefix} ` : "";
  const suffixText = suffix ? `${getSuffixSeparator(suffix)}${suffix}` : "";

  return `${sign}${prefixText}${formattedNumber}${suffixText}`;
}

type MonthlyTargetLike = {
  month_number?: number;
  monthNumber?: number;
  target_value?: number;
  targetValue?: number;
};

export type IndicatorGoalDisplayInput = IndicatorValueFormat & {
  goalLabel: string;
  goalValue?: number | null;
  goalMode?: string | null;
  monthlyTargets?: MonthlyTargetLike[] | null;
  /** Metas comparáveis por filial (01/02) ou consolidado — espelha `gaps` / `realized`. */
  goals?: Record<string, number | null> | null;
};

function resolveCompetenceMonth(competence?: string | null): number | null {
  if (!competence) return null;

  const normalized = competence.trim();

  const isoMatch = normalized.match(/^(\d{4})-(\d{2})$/);
  if (isoMatch) {
    const month = Number(isoMatch[2]);
    return month >= 1 && month <= 12 ? month : null;
  }

  const brMatch = normalized.match(/^(\d{2})\/(\d{4}|\d{2})$/);
  if (brMatch) {
    const month = Number(brMatch[1]);
    return month >= 1 && month <= 12 ? month : null;
  }

  return null;
}

function getMonthlyTargetValue(
  monthlyTargets: MonthlyTargetLike[] | null | undefined,
  monthNumber: number | null,
): number | null {
  if (!monthNumber) return null;

  const target = (monthlyTargets ?? []).find((item) => {
    const itemMonth = item.month_number ?? item.monthNumber;
    return Number(itemMonth) === monthNumber;
  });

  const value = target?.target_value ?? target?.targetValue;

  if (value === null || value === undefined) return null;

  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

/** Rótulos PT-BR para chaves de `realized` / `gaps` (comercial, filiais TOTVS, etc.). */
const UNIT_SCOPE_LABELS: Record<string, string> = {
  matrix: "Matriz",
  branch: "Filial",
};

function formatBranchUnitLabel(
  scopeKey: string,
  options: FormatIndicatorValueOptions = {},
) {
  const normalized = scopeKey.trim();
  const activeBranch = (options.activeBranch ?? "").trim();

  if (activeBranch && normalized === activeBranch) {
    return options.filterViewScopeLabel ?? `Filial ${activeBranch}`;
  }

  return UNIT_SCOPE_LABELS[normalized] ?? normalized;
}

function listBranchScopeKeys(values: Record<string, number | null>): string[] {
  return Object.keys(values)
    .filter((key) => key.trim() !== "" && key !== "consolidated")
    .sort();
}

/** Com filtro de filial ativo, exibe só a unidade selecionada (sem `01 | 02`). */
function filterScopedValuesByActiveBranch(
  values: Record<string, number | null>,
  activeBranch?: string,
): Record<string, number | null> {
  const branch = (activeBranch ?? "").trim();
  if (!branch || !(branch in values)) {
    return values;
  }

  return { [branch]: values[branch] };
}

/** Deptos consolidados (Engenharia, etc.): mesmo valor em filial e consolidado → só rótulo Consolidado. */
function consolidatedOnlyDisplayValues(
  values: Record<string, number | null> | undefined,
): Record<string, number | null> | null {
  if (!values || values.consolidated === null || values.consolidated === undefined) {
    return null;
  }

  const branchKeys = listBranchScopeKeys(values);
  if (!branchKeys.length) {
    return null;
  }

  const consolidated = values.consolidated;
  const allMatch = branchKeys.every((code) => values[code] === consolidated);
  if (!allMatch) {
    return null;
  }

  return { consolidated };
}

export function hasMultiBranchValues(
  values: Record<string, number | null> | undefined,
): boolean {
  if (!values) return false;

  return listBranchScopeKeys(values).length >= 2;
}

export function hasBranchScopeValues(
  values: Record<string, number | null> | undefined,
): boolean {
  if (!values) return false;

  return listBranchScopeKeys(values).length >= 1;
}

const SEMANTIC_SCOPE_KEYS = new Set([
  "consolidated",
  "per_unit",
  "average_of_units",
]);

function getSemanticScopeLabel(
  key: string,
  options: FormatIndicatorValueOptions = {},
): string {
  if (key === "consolidated" && options.filterViewScopeLabel) {
    return options.filterViewScopeLabel;
  }

  switch (key) {
    case "consolidated":
      return "Consolidado";
    case "per_unit":
      return "Por unidade";
    case "average_of_units":
      return "Média das unidades";
    default:
      return key;
  }
}

/** Formata mapa de realizado/gap: filiais via `01: … | 02: …`; chaves semânticas sem duplicar rótulo. */
export function formatScopeAwareMetric(
  values: Record<string, number | null> | undefined,
  format: IndicatorValueFormat = {},
  options: FormatIndicatorValueOptions = {},
): string {
  if (!values || !Object.keys(values).length) {
    return options.fallback ?? MISSING_VALUE_LABEL;
  }

  values = filterScopedValuesByActiveBranch(values, options.activeBranch);

  const consolidatedOnly = consolidatedOnlyDisplayValues(values);
  if (consolidatedOnly) {
    return `${getSemanticScopeLabel("consolidated", options)}: ${formatIndicatorValue(
      consolidatedOnly.consolidated,
      format,
      options,
    )}`;
  }

  if (hasBranchScopeValues(values)) {
    return formatBranchScopedMetric(values, format, options);
  }

  return Object.entries(values)
    .map(([key, value]) => {
      const label = SEMANTIC_SCOPE_KEYS.has(key)
        ? getSemanticScopeLabel(key, options)
        : formatBranchUnitLabel(key, options);
      return `${label}: ${formatIndicatorValue(value, format, options)}`;
    })
    .join(" · ");
}

export function formatBranchScopedMetric(
  values: Record<string, number | null> | undefined,
  format: IndicatorValueFormat = {},
  options: FormatIndicatorValueOptions = {},
): string {
  if (!values || !Object.keys(values).length) {
    return options.fallback ?? MISSING_VALUE_LABEL;
  }

  const branchParts = listBranchScopeKeys(values).map(
    (code) =>
      `${formatBranchUnitLabel(code, options)}: ${formatIndicatorValue(
        values[code],
        format,
        options,
      )}`,
  );

  if (branchParts.length >= 2) {
    return branchParts.join(" | ");
  }

  if (branchParts.length === 1) {
    return branchParts[0];
  }

  if ("consolidated" in values) {
    return formatIndicatorValue(values.consolidated, format, options);
  }

  return Object.entries(values)
    .map(
      ([key, value]) =>
        `${formatBranchUnitLabel(key, options)}: ${formatIndicatorValue(value, format, options)}`,
    )
    .join(" | ");
}

export type IndicatorScopedMetricsInput = {
  gap?: number | null;
  gaps?: Record<string, number | null>;
  realized?: Record<string, number | null>;
  value?: number | null;
  currentValue?: number | null;
  hasValue?: boolean;
};

export type IndicatorDisplayContext = {
  filterViewScopeLabel?: string;
  activeBranch?: string;
};

function mergeDisplayContext(
  options: FormatIndicatorValueOptions = {},
  displayContext?: IndicatorDisplayContext,
): FormatIndicatorValueOptions {
  return {
    ...options,
    filterViewScopeLabel:
      displayContext?.filterViewScopeLabel ?? options.filterViewScopeLabel,
    activeBranch: displayContext?.activeBranch ?? options.activeBranch,
  };
}

function hasScopedMetricMap(
  values: Record<string, number | null> | undefined,
): boolean {
  if (!values || !Object.keys(values).length) {
    return false;
  }

  return (
    hasBranchScopeValues(values) ||
    hasMultiBranchValues(values) ||
    Object.keys(values).length > 0
  );
}

/** Gap com filiais (`01: … | 02: …`) quando `gaps` vier da API; senão valor consolidado. */
export function formatIndicatorGapDisplay(
  metrics: Pick<IndicatorScopedMetricsInput, "gap" | "gaps">,
  format: IndicatorValueFormat = {},
  displayContext?: IndicatorDisplayContext,
): string {
  const gaps = metrics.gaps ?? {};
  const scopedOptions = mergeDisplayContext({ signed: true }, displayContext);

  if (hasScopedMetricMap(gaps)) {
    return formatScopeAwareMetric(gaps, format, scopedOptions);
  }

  return formatIndicatorValue(metrics.gap ?? null, format, { signed: true });
}

/** Realizado / valor atual com o mesmo padrão de escopo da meta. */
export function formatIndicatorRealizedDisplay(
  metrics: Pick<
    IndicatorScopedMetricsInput,
    "realized" | "value" | "currentValue" | "hasValue"
  >,
  format: IndicatorValueFormat = {},
  displayContext?: IndicatorDisplayContext,
): string {
  const realized = metrics.realized ?? {};
  const scopedOptions = mergeDisplayContext({}, displayContext);

  if (hasScopedMetricMap(realized)) {
    return formatScopeAwareMetric(realized, format, scopedOptions);
  }

  const single = metrics.currentValue ?? metrics.value ?? null;

  if (single !== null && single !== undefined) {
    return formatIndicatorValue(single, format);
  }

  if (metrics.hasValue === false) {
    return MISSING_VALUE_LABEL;
  }

  return "—";
}

/** Linha de contexto (subtítulo) alinhada à coluna Meta. */
export function formatIndicatorMetaGoalLine(
  indicator: IndicatorGoalDisplayInput,
  competence?: string | null,
  displayContext?: IndicatorDisplayContext,
): string {
  return `Meta ${formatIndicatorGoalValue(indicator, competence, displayContext)}`;
}

export function formatIndicatorGoalValue(
  indicator: IndicatorGoalDisplayInput,
  competence?: string | null,
  displayContext?: IndicatorDisplayContext,
): string {
  const valueFormat: IndicatorValueFormat = {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };
  const scopedOptions = mergeDisplayContext({}, displayContext);
  const goals = filterScopedValuesByActiveBranch(
    indicator.goals ?? {},
    scopedOptions.activeBranch,
  );

  if (hasScopedMetricMap(goals)) {
    return formatScopeAwareMetric(goals, valueFormat, scopedOptions);
  }

  if (indicator.goalMode !== "monthly_curve") {
    return indicator.goalLabel;
  }

  const monthNumber = resolveCompetenceMonth(competence);
  const monthlyTarget = getMonthlyTargetValue(
    indicator.monthlyTargets,
    monthNumber,
  );

  if (monthlyTarget === null) {
    return indicator.goalLabel;
  }

  return formatIndicatorValue(monthlyTarget, valueFormat);
}