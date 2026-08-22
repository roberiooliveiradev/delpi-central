import { useMemo } from "react";

import {
  fetchCostCenterEntries,
  fetchCostCenterFilters,
  fetchCostCenterRankingCenters,
  fetchCostCenterRankingSuppliers,
  fetchCostCenterSeries,
  fetchCostCenterSummary,
} from "../api/financialApi";
import { copy } from "../content/copy";
import type {
  CostCenterEntriesPayload,
  CostCenterFiltersPayload,
  CostCenterRankingItem,
  CostCenterSeriesPoint,
  CostCenterSummary,
  FinancialBranch,
} from "../types";
import { useAsyncResource } from "./useAsyncResource";

export type CostCenterPageFilters = {
  branch: FinancialBranch;
  startDate: string | null;
  endDate: string | null;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  search: string | null;
  page: number;
  sortBy: string;
  sortDir: "asc" | "desc";
};

export type CostCenterSectionErrors = Partial<{
  filters: string;
  summary: string;
  series: string;
  centers: string;
  suppliers: string;
  entries: string;
}>;

export type CostCenterBundle = {
  filters: CostCenterFiltersPayload;
  summary: CostCenterSummary;
  series: CostCenterSeriesPoint[];
  centers: CostCenterRankingItem[];
  suppliers: CostCenterRankingItem[];
  entries: CostCenterEntriesPayload;
  sectionErrors: CostCenterSectionErrors;
};

function errorMessage(reason: unknown, fallback: string): string {
  return reason instanceof Error ? reason.message : fallback;
}

function emptyFilters(): CostCenterFiltersPayload {
  return {
    period: { startDate: "", endDate: "" },
    branch: null,
    branches: [],
    costCenters: [],
    suppliers: [],
  };
}

function emptyEntries(filters: CostCenterPageFilters): CostCenterEntriesPayload {
  return {
    period: { startDate: "", endDate: "" },
    branch: null,
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

export function useCostCenters(filters: CostCenterPageFilters) {
  const key = useMemo(
    () =>
      [
        filters.branch,
        filters.startDate,
        filters.endDate,
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

  return useAsyncResource<CostCenterBundle>(
    async (signal) => {
      const shared = {
        branch: filters.branch,
        startDate: filters.startDate,
        endDate: filters.endDate,
        costCenter: filters.costCenter,
        supplierCode: filters.supplierCode,
        supplierStore: filters.supplierStore,
        excludeMpProducts: filters.excludeMp,
        signal,
      };
      const sectionErrors: CostCenterSectionErrors = {};

      const [catalogResult, summaryResult, entriesResult] = await Promise.allSettled([
        fetchCostCenterFilters(shared),
        fetchCostCenterSummary(shared),
        fetchCostCenterEntries({
          ...shared,
          search: filters.search,
          page: filters.page,
          sortBy: filters.sortBy,
          sortDir: filters.sortDir,
        }),
      ]);

      const catalog =
        catalogResult.status === "fulfilled" ? catalogResult.value : emptyFilters();
      if (catalogResult.status === "rejected") {
        sectionErrors.filters = errorMessage(
          catalogResult.reason,
          copy.costCenters.loadError,
        );
      }

      if (summaryResult.status === "rejected" && entriesResult.status === "rejected") {
        throw summaryResult.reason;
      }

      const summary =
        summaryResult.status === "fulfilled"
          ? summaryResult.value
          : entriesResult.status === "fulfilled"
            ? {
                period: entriesResult.value.period,
                branch: entriesResult.value.branch,
                totalAmount: 0,
                entryCount: entriesResult.value.pagination.totalItems,
                costCenterCount: 0,
                supplierCount: 0,
                averageTicket: 0,
                largestEntry: 0,
              }
            : null;

      if (!summary) {
        throw entriesResult.status === "rejected" ? entriesResult.reason : copy.costCenters.loadError;
      }

      if (summaryResult.status === "rejected") {
        sectionErrors.summary = errorMessage(summaryResult.reason, copy.costCenters.loadError);
      }

      const entries =
        entriesResult.status === "fulfilled" ? entriesResult.value : emptyEntries(filters);
      if (entriesResult.status === "rejected") {
        sectionErrors.entries = errorMessage(entriesResult.reason, copy.costCenters.loadError);
      }

      const [seriesResult, centersResult, suppliersResult] = await Promise.allSettled([
        fetchCostCenterSeries(shared),
        fetchCostCenterRankingCenters(shared),
        fetchCostCenterRankingSuppliers(shared),
      ]);

      const series = seriesResult.status === "fulfilled" ? seriesResult.value.items : [];
      if (seriesResult.status === "rejected") {
        sectionErrors.series = errorMessage(seriesResult.reason, copy.costCenters.loadError);
      }

      const centers = centersResult.status === "fulfilled" ? centersResult.value.items : [];
      if (centersResult.status === "rejected") {
        sectionErrors.centers = errorMessage(centersResult.reason, copy.costCenters.loadError);
      }

      const suppliers = suppliersResult.status === "fulfilled" ? suppliersResult.value.items : [];
      if (suppliersResult.status === "rejected") {
        sectionErrors.suppliers = errorMessage(suppliersResult.reason, copy.costCenters.loadError);
      }

      return {
        filters: catalog,
        summary,
        series,
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
