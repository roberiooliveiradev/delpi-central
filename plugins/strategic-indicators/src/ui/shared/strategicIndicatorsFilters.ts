export type StrategicIndicatorsViewMode = "consolidated" | "branch";

export const STRATEGIC_INDICATORS_BRANCH_OPTIONS = [
  { value: "01", label: "01" },
  { value: "02", label: "02" },
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

/** Rótulo da visão ativa nos painéis (filtro consolidado vs filial). */
export function getFilterViewScopeLabel(
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): string {
  if (viewMode === "branch" && branch.trim()) {
    return `Filial ${branch.trim()}`;
  }

  return "Consolidado";
}

export function isStrategicIndicatorsDepartmentsRoute(
  pathname = typeof window !== "undefined" ? window.location.pathname : "",
): boolean {
  return pathname.includes("/strategic-indicators/departments");
}

export function getDefaultMonthsToCompare(
  pathname = typeof window !== "undefined" ? window.location.pathname : "",
): number {
  return isStrategicIndicatorsDepartmentsRoute(pathname) ? 3 : 6;
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