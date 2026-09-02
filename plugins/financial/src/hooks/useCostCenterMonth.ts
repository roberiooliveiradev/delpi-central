import { useCallback, useMemo } from "react";

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
import {
  costCenterMonthDashboardKey,
  costCenterMonthEntriesKey,
} from "./costCenterMonthKeys";
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

export {
  costCenterMonthDashboardKey,
  costCenterMonthEntriesKey,
} from "./costCenterMonthKeys";

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

type CostCenterMonthDashboard = Omit<CostCenterMonthBundle, "entries">;

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
  const dashboardKey = useMemo(() => costCenterMonthDashboardKey(filters), [filters]);
  const entriesKey = useMemo(() => costCenterMonthEntriesKey(filters), [filters]);

  const dashboard = useAsyncResource<CostCenterMonthDashboard>(
    async (signal) => {
      const period = monthPeriodRange(filters.month);
      if (!period) throw new Error(copy.costCenters.monthDetail.invalidMonth);

      const previousMonth = previousYearMonth(filters.month);
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

      // Sem o resumo do mês anterior aqui: ele competia no TOTVS com summary/rankings
      // e empurrava o BFF para 502 (timeout). Comparativo carrega depois.
      // Com CC filtrado, ranking de centros é redundante (igual ao legado).
      const rankingCentersPromise = filters.costCenter
        ? Promise.resolve({ items: [] as CostCenterRankingItem[] })
        : fetchCostCenterRankingCenters(shared);

      const [summaryResult, centersResult, suppliersResult] = await Promise.allSettled([
        fetchCostCenterSummary(shared),
        rankingCentersPromise,
        fetchCostCenterRankingSuppliers(shared),
      ]);

      if (
        summaryResult.status === "rejected" &&
        centersResult.status === "rejected" &&
        suppliersResult.status === "rejected"
      ) {
        throw summaryResult.reason;
      }

      const summary =
        summaryResult.status === "fulfilled"
          ? summaryResult.value
          : emptySummary(period, filters.branch);
      if (summaryResult.status === "rejected") {
        sectionErrors.summary = errorMessage(summaryResult.reason, copy.costCenters.loadError);
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
        month: filters.month,
        previousMonth,
        period,
        summary,
        previousSummary: null,
        centers,
        suppliers,
        sectionErrors,
      };
    },
    [dashboardKey],
    copy.costCenters.loadError,
  );

  const previousReady = Boolean(dashboard.data) && !dashboard.loading;
  const previous = useAsyncResource<CostCenterSummary | null>(
    async (signal) => {
      if (!previousReady || !dashboard.data?.previousMonth) return null;
      const previousPeriod = monthPeriodRange(dashboard.data.previousMonth);
      if (!previousPeriod) return null;
      return fetchCostCenterSummary({
        branch: filters.branch,
        startDate: previousPeriod.startDate,
        endDate: previousPeriod.endDate,
        costCenter: filters.costCenter,
        supplierCode: filters.supplierCode,
        supplierStore: filters.supplierStore,
        excludeMpProducts: filters.excludeMp,
        signal,
      });
    },
    [dashboardKey, previousReady, dashboard.data?.previousMonth],
    copy.costCenters.loadError,
  );

  const entries = useAsyncResource<CostCenterEntriesPayload>(
    async (signal) => {
      const period = monthPeriodRange(filters.month);
      if (!period) throw new Error(copy.costCenters.monthDetail.invalidMonth);

      return fetchCostCenterEntries({
        branch: filters.branch,
        startDate: period.startDate,
        endDate: period.endDate,
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

  const data = useMemo<CostCenterMonthBundle | null>(() => {
    if (!dashboard.data) return null;
    return {
      ...dashboard.data,
      previousSummary: previous.error ? null : (previous.data ?? null),
      entries: entries.data ?? emptyEntries(filters, dashboard.data.period),
      sectionErrors: {
        ...dashboard.data.sectionErrors,
        ...(previous.error ? { previousSummary: previous.error } : {}),
        ...(entries.error ? { entries: entries.error } : {}),
      },
    };
  }, [
    dashboard.data,
    previous.data,
    previous.error,
    entries.data,
    entries.error,
    filters,
  ]);

  const reload = useCallback(() => {
    dashboard.reload();
    previous.reload();
    entries.reload();
  }, [dashboard.reload, previous.reload, entries.reload]);

  return {
    data,
    /** Carregamento do painel (KPIs + rankings). */
    loading: dashboard.loading,
    /** Só a grade de lançamentos (paginação/ordenação/busca). */
    entriesLoading: entries.loading,
    error: dashboard.error,
    reload,
  };
}
