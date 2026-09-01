import { useMemo } from "react";

import {
  fetchCostCenterEntries,
  fetchCostCenterRankingCenters,
  fetchCostCenterRankingSuppliers,
  fetchCostCenterSummary,
} from "../api/financialApi";
import { copy } from "../content/copy";
import type {
  CostCenterEntriesPayload,
  CostCenterRankingItem,
  CostCenterSummary,
  FinancialBranch,
  Period,
} from "../types";
import { monthPeriodRange, previousYearMonth, type MonthPeriod } from "../utils/monthPeriod";
import { useAsyncResource } from "./useAsyncResource";

export type CostCenterMonthFilters = {
  branch: FinancialBranch;
  month: string;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  search: string | null;
  page: number;
  sortBy: string;
  sortDir: "asc" | "desc";
};

export type CostCenterMonthSectionErrors = Partial<{
  summary: string;
  previousSummary: string;
  centers: string;
  suppliers: string;
  entries: string;
}>;

export type CostCenterMonthBundle = {
  month: string;
  previousMonth: string | null;
  period: MonthPeriod;
  summary: CostCenterSummary;
  /** `null` quando o mês anterior falha ou não existe — comparativo fica oculto. */
  previousSummary: CostCenterSummary | null;
  centers: CostCenterRankingItem[];
  suppliers: CostCenterRankingItem[];
  entries: CostCenterEntriesPayload;
  sectionErrors: CostCenterMonthSectionErrors;
};

function errorMessage(reason: unknown, fallback: string): string {
  return reason instanceof Error ? reason.message : fallback;
}

function periodPayload(period: MonthPeriod): Period {
  return {
    startDate: period.startDate,
    endDate: period.endDate,
    endDateExclusive: null,
    label: null,
  };
}

function emptyEntries(
  filters: CostCenterMonthFilters,
  period: MonthPeriod,
): CostCenterEntriesPayload {
  return {
    period: periodPayload(period),
    branch: filters.branch,
    pagination: {
      page: filters.page,
      pageSize: 50,
      totalItems: 0,
      totalPages: 0,
      hasNext: false,
      hasPrevious: false,
      isComplete: true,
    },
    sort: { sortBy: filters.sortBy, sortDir: filters.sortDir },
    filters: {
      costCenter: filters.costCenter,
      supplierCode: filters.supplierCode,
      supplierStore: filters.supplierStore,
      search: filters.search,
    },
    items: [],
  };
}

function emptySummary(period: MonthPeriod, branch: FinancialBranch): CostCenterSummary {
  return {
    period: periodPayload(period),
    branch,
    totalAmount: 0,
    entryCount: 0,
    costCenterCount: 0,
    supplierCount: 0,
    averageTicket: 0,
    largestEntry: 0,
  };
}

export function useCostCenterMonth(filters: CostCenterMonthFilters) {
  const key = useMemo(
    () =>
      [
        filters.branch,
        filters.month,
        filters.costCenter,
        filters.supplierCode,
        filters.supplierStore,
        filters.excludeMp,
        filters.search,
        filters.page,
        filters.sortBy,
        filters.sortDir,
      ].join("|"),
    [filters],
  );

  return useAsyncResource<CostCenterMonthBundle>(
    async (signal) => {
      const period = monthPeriodRange(filters.month);
      if (!period) throw new Error(copy.costCenters.monthDetail.invalidMonth);

      const previousMonth = previousYearMonth(filters.month);
      const previousPeriod = previousMonth ? monthPeriodRange(previousMonth) : null;

      const scope = {
        branch: filters.branch,
        costCenter: filters.costCenter,
        supplierCode: filters.supplierCode,
        supplierStore: filters.supplierStore,
        excludeMpProducts: filters.excludeMp,
        signal,
      };
      const shared = { ...scope, startDate: period.startDate, endDate: period.endDate };
      const sectionErrors: CostCenterMonthSectionErrors = {};

      const [summaryResult, entriesResult, previousResult] = await Promise.allSettled([
        fetchCostCenterSummary(shared),
        fetchCostCenterEntries({
          ...shared,
          search: filters.search,
          page: filters.page,
          sortBy: filters.sortBy,
          sortDir: filters.sortDir,
        }),
        previousPeriod
          ? fetchCostCenterSummary({
              ...scope,
              startDate: previousPeriod.startDate,
              endDate: previousPeriod.endDate,
            })
          : Promise.resolve(null),
      ]);

      if (summaryResult.status === "rejected" && entriesResult.status === "rejected") {
        throw summaryResult.reason;
      }

      const summary =
        summaryResult.status === "fulfilled"
          ? summaryResult.value
          : emptySummary(period, filters.branch);
      if (summaryResult.status === "rejected") {
        sectionErrors.summary = errorMessage(summaryResult.reason, copy.costCenters.loadError);
      }

      const entries =
        entriesResult.status === "fulfilled"
          ? entriesResult.value
          : emptyEntries(filters, period);
      if (entriesResult.status === "rejected") {
        sectionErrors.entries = errorMessage(entriesResult.reason, copy.costCenters.loadError);
      }

      const previousSummary =
        previousResult.status === "fulfilled" ? previousResult.value : null;
      if (previousResult.status === "rejected") {
        sectionErrors.previousSummary = errorMessage(
          previousResult.reason,
          copy.costCenters.loadError,
        );
      }

      const [centersResult, suppliersResult] = await Promise.allSettled([
        fetchCostCenterRankingCenters(shared),
        fetchCostCenterRankingSuppliers(shared),
      ]);

      const centers = centersResult.status === "fulfilled" ? centersResult.value.items : [];
      if (centersResult.status === "rejected") {
        sectionErrors.centers = errorMessage(centersResult.reason, copy.costCenters.loadError);
      }

      const suppliers = suppliersResult.status === "fulfilled" ? suppliersResult.value.items : [];
      if (suppliersResult.status === "rejected") {
        sectionErrors.suppliers = errorMessage(
          suppliersResult.reason,
          copy.costCenters.loadError,
        );
      }

      return {
        month: filters.month,
        previousMonth,
        period,
        summary,
        previousSummary,
        centers,
        suppliers,
        entries,
        sectionErrors,
      };
    },
    [key],
    copy.costCenters.loadError,
  );
}
