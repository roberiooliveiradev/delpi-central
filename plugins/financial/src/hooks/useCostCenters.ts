import { useCallback, useMemo } from "react";

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
import {
  costCenterPageDashboardKey,
  costCenterPageEntriesKey,
} from "./costCenterPageKeys";
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

type CostCenterPageDashboard = Omit<CostCenterBundle, "entries">;

export {
  costCenterPageDashboardKey,
  costCenterPageEntriesKey,
} from "./costCenterPageKeys";

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
  const dashboardKey = useMemo(() => costCenterPageDashboardKey(filters), [filters]);
  const entriesKey = useMemo(() => costCenterPageEntriesKey(filters), [filters]);

  const dashboard = useAsyncResource<CostCenterPageDashboard>(
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

      // Uma onda: igual ao legado após /filtros — sem waterfall wave1→wave2.
      const rankingCentersPromise = filters.costCenter
        ? Promise.resolve({ items: [] as CostCenterRankingItem[] })
        : fetchCostCenterRankingCenters(shared);

      const [catalogResult, summaryResult, seriesResult, centersResult, suppliersResult] =
        await Promise.allSettled([
          fetchCostCenterFilters(shared),
          fetchCostCenterSummary(shared),
          fetchCostCenterSeries(shared),
          rankingCentersPromise,
          fetchCostCenterRankingSuppliers(shared),
        ]);

      const catalog =
        catalogResult.status === "fulfilled" ? catalogResult.value : emptyFilters();
      if (catalogResult.status === "rejected") {
        sectionErrors.filters = errorMessage(
          catalogResult.reason,
          copy.costCenters.loadError,
        );
      }

      if (summaryResult.status === "rejected") {
        throw summaryResult.reason;
      }

      const summary = summaryResult.value;

      const series = seriesResult.status === "fulfilled" ? seriesResult.value.items : [];
      if (seriesResult.status === "rejected") {
        sectionErrors.series = errorMessage(seriesResult.reason, copy.costCenters.loadError);
      }

      const centers = centersResult.status === "fulfilled" ? centersResult.value.items : [];
      if (centersResult.status === "rejected") {
        sectionErrors.centers = errorMessage(centersResult.reason, copy.costCenters.loadError);
      }

      const suppliers =
        suppliersResult.status === "fulfilled" ? suppliersResult.value.items : [];
      if (suppliersResult.status === "rejected") {
        sectionErrors.suppliers = errorMessage(
          suppliersResult.reason,
          copy.costCenters.loadError,
        );
      }

      return {
        filters: catalog,
        summary,
        series,
        centers,
        suppliers,
        sectionErrors,
      };
    },
    [dashboardKey],
    copy.costCenters.loadError,
  );

  const entries = useAsyncResource<CostCenterEntriesPayload>(
    async (signal) => {
      return fetchCostCenterEntries({
        branch: filters.branch,
        startDate: filters.startDate,
        endDate: filters.endDate,
        costCenter: filters.costCenter,
        supplierCode: filters.supplierCode,
        supplierStore: filters.supplierStore,
        excludeMpProducts: filters.excludeMp,
        search: filters.search,
        page: filters.page,
        sortBy: filters.sortBy,
        sortDir: filters.sortDir,
        signal,
      });
    },
    [entriesKey],
    copy.costCenters.loadError,
  );

  const data = useMemo<CostCenterBundle | null>(() => {
    if (!dashboard.data) return null;
    return {
      ...dashboard.data,
      entries: entries.data ?? emptyEntries(filters),
      sectionErrors: {
        ...dashboard.data.sectionErrors,
        ...(entries.error ? { entries: entries.error } : {}),
      },
    };
  }, [dashboard.data, entries.data, entries.error, filters]);

  const reload = useCallback(() => {
    dashboard.reload();
    entries.reload();
  }, [dashboard.reload, entries.reload]);

  return {
    data,
    loading: dashboard.loading,
    entriesLoading: entries.loading,
    error: dashboard.error,
    reload,
  };
}
