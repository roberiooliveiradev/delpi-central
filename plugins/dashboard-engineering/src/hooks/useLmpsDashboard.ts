import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getLmpsDashboardSummary,
  getLmpsDashboardCharts,
  getLmpsDashboardItems,
} from "../api/engineeringApi";
import type {
  LmpDashboardItem,
  LmpsDashboardCharts,
  LmpsDashboardParams,
  LmpsDashboardSummary,
} from "../types/lmp";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";
import { inputDateToLmpApi } from "../utils/lmpDates";
import {
  EMPTY_REQUEST_PROGRESS,
  type RequestProgress,
} from "../utils/loadingProgress";

export const LMP_DASHBOARD_PAGE_SIZE = 50;

type UseLmpsDashboardParams = Omit<LmpsDashboardParams, "page" | "page_size">;

export function useLmpsDashboard(params: UseLmpsDashboardParams) {
  const [summary, setSummary] = useState<LmpsDashboardSummary | null>(null);
  const [charts, setCharts] = useState<LmpsDashboardCharts | null>(null);
  const [items, setItems] = useState<LmpDashboardItem[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(LMP_DASHBOARD_PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [page, setPage] = useState(1);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const stableParams = useMemo(
    () => ({
      date_start: inputDateToLmpApi(params.date_start),
      date_end: inputDateToLmpApi(params.date_end),
      branch: params.branch,
      listing_type: params.listing_type,
      status: params.status,
    }),
    [
      params.date_start,
      params.date_end,
      params.branch,
      params.listing_type,
      params.status,
    ]
  );

  useEffect(() => {
    setPage(1);
  }, [
    stableParams.branch,
    stableParams.date_end,
    stableParams.date_start,
    stableParams.listing_type,
    stableParams.status,
  ]);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = summary !== null || charts !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        const TOTAL_PHASES = 3;
        setRequestProgress({ completed: 0, total: TOTAL_PHASES });

        // Phase 1: Summary (KPIs)
        const summaryResult = await getLmpsDashboardSummary(
          stableParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setSummary(summaryResult);
        setRequestProgress({ completed: 1, total: TOTAL_PHASES });

        // Phase 2: Charts
        const chartsResult = await getLmpsDashboardCharts(
          stableParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setCharts(chartsResult);
        setRequestProgress({ completed: 2, total: TOTAL_PHASES });

        setLoading(false);
        setRefreshing(false);

        // Phase 3: Items (paginated) — loaded in background
        setItemsLoading(true);
        const itemsResult = await getLmpsDashboardItems(
          { ...stableParams, page, page_size: LMP_DASHBOARD_PAGE_SIZE },
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setItems(itemsResult.items);
        setTotal(itemsResult.total);
        setCurrentPage(itemsResult.page);
        setPageSize(itemsResult.page_size);
        setRequestProgress({ completed: 3, total: TOTAL_PHASES });
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
          setLoading(false);
          setRefreshing(false);
        }
      } finally {
        if (!controller.signal.aborted) {
          setItemsLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    stableParams.branch,
    stableParams.date_end,
    stableParams.date_start,
    stableParams.listing_type,
    stableParams.status,
    page,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    data: summary ? { items, total, page: currentPage, page_size: pageSize, summary, charts } : null,
    items,
    summary,
    charts,
    total,
    page: currentPage,
    pageSize,
    setPage,
    loading,
    itemsLoading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
