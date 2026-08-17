import { formatFilterViewScopeLabel } from "./operationalUnitLabels";

export type StrategicIndicatorsViewMode = "consolidated" | "branch";

export const STRATEGIC_INDICATORS_BRANCH_OPTIONS = [
  { value: "01", label: "Santa Catarina" },
  { value: "02", label: "Espírito Santo" },
];

export function getCurrentStrategicIndicatorsMonthValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function buildStrategicIndicatorsMonthRange(monthValue: string) {
  if (!monthValue) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const [yearStr, monthStr] = monthValue.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (!year || !month) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const firstDay = `01-${String(month).padStart(2, "0")}-${year}`;
  const lastDayDate = new Date(year, month, 0);
  const lastDay = `${String(lastDayDate.getDate()).padStart(2, "0")}-${String(
    month,
  ).padStart(2, "0")}-${year}`;

  return {
    startDate: firstDay,
    endDate: lastDay,
  };
}

export function resolveStrategicIndicatorsBranch(
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
) {
  return viewMode === "branch" ? branch : undefined;
}

/** Rótulo da visão ativa nos painéis (filtro consolidado vs unidade). */
export function getFilterViewScopeLabel(
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): string {
  return formatFilterViewScopeLabel(viewMode, branch);
}

export function isStrategicIndicatorsDepartmentsRoute(
  pathname = typeof window !== "undefined" ? window.location.pathname : "",
): boolean {
  return pathname.includes("/strategic-indicators/departments");
}

/** Janela canônica de materialização / série (alinhada à API SI). */
export const SI_DEFAULT_SERIES_MONTHS = 6;

/** Janela de exibição default só na árvore de departamentos. */
export const SI_DEPARTMENTS_DISPLAY_MONTHS = 3;

export function getDefaultMonthsToCompare(
  pathname = typeof window !== "undefined" ? window.location.pathname : "",
): number {
  return isStrategicIndicatorsDepartmentsRoute(pathname)
    ? SI_DEPARTMENTS_DISPLAY_MONTHS
    : SI_DEFAULT_SERIES_MONTHS;
}

export function formatComparisonMonthsLabel(months: number): string {
  return `${months} ${months === 1 ? "mês" : "meses"}`;
}

export function sliceTrendPoints<T>(points: readonly T[], months: number): T[] {
  if (months <= 0 || points.length <= months) {
    return [...points];
  }

  return points.slice(-months);
}