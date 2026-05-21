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

export type IndicatorGoalDisplayInput = {
  goalLabel: string;
  goalValue?: number | null;
  goalMode?: string | null;
  monthlyTargets?: MonthlyTargetLike[] | null;
  valueUnit?: string | null;
  valuePrefix?: string | null;
  valueSuffix?: string | null;
  valueDecimals?: number | null;
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

function formatBranchUnitLabel(branchCode: string) {
  return branchCode.trim();
}

function listBranchScopeKeys(values: Record<string, number | null>): string[] {
  return Object.keys(values)
    .filter((key) => key.trim() !== "" && key !== "consolidated")
    .sort();
}

export function hasMultiBranchValues(
  values: Record<string, number | null> | undefined,
): boolean {
  if (!values) return false;

  return listBranchScopeKeys(values).length >= 2;
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
      `${formatBranchUnitLabel(code)}: ${formatIndicatorValue(
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
        `${formatBranchUnitLabel(key)}: ${formatIndicatorValue(value, format, options)}`,
    )
    .join(" | ");
}

export function formatIndicatorGoalValue(
  indicator: IndicatorGoalDisplayInput,
  competence?: string | null,
): string {
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

  return formatIndicatorValue(monthlyTarget, {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  });
}