function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function getDefaultLast12MonthsRange(referenceDate = new Date()): {
  startDate: string;
  endDate: string;
} {
  const endDate = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 11, 1);

  return {
    startDate: formatIsoDate(startDate),
    endDate: formatIsoDate(endDate),
  };
}

import type { DespesasQueryFilters, FilterFormState } from "../types/despesasCentroCusto";

export function filtersFromFormState(state: FilterFormState): DespesasQueryFilters {
  const [supplierCode = "", supplierStore = ""] = state.supplierKey
    ? state.supplierKey.split("|")
    : [];

  return {
    startDate: state.startDate,
    endDate: state.endDate,
    branch: state.branch || undefined,
    costCenter: state.costCenter || undefined,
    supplierCode: supplierCode || undefined,
    supplierStore: supplierStore || undefined,
  };
}

export function createDefaultFilterFormState(referenceDate = new Date()): FilterFormState {
  const range = getDefaultLast12MonthsRange(referenceDate);
  return {
    startDate: range.startDate,
    endDate: range.endDate,
    branch: "",
    costCenter: "",
    supplierKey: "",
  };
}
