export type StrategicIndicatorsViewMode = "consolidated" | "branch";

export const STRATEGIC_INDICATORS_BRANCH_OPTIONS = [
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
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