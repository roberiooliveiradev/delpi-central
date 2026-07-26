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
  const [pageSize, setPageSizeState] = useState(LMP_DASHBOARD_PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [itemsRefreshing, setItemsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [page, setPage] = useState(1);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const stableParams = useMemo(
    () => ({
      start_date: inputDateToLmpApi(params.start_date),
      end_date: inputDateToLmpApi(params.end_date),
      branch: params.branch,
      listing_type: params.listing_type,
      status: params.status,
    }),
    [
      params.start_date,
      params.end_date,
      params.branch,
      params.listing_type,
      params.status,
    ]
  );

  useEffect(() => {
    setPage(1);
  }, [
    stableParams.branch,
    stableParams.end_date,
    stableParams.start_date,
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

        const TOTAL_PHASES = 2;
        setRequestProgress({ completed: 0, total: TOTAL_PHASES });

        const summaryResult = await getLmpsDashboardSummary(
          stableParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setSummary(summaryResult);
        setRequestProgress({ completed: 1, total: TOTAL_PHASES });

        const chartsResult = await getLmpsDashboardCharts(
          stableParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setCharts(chartsResult);
        setRequestProgress({ completed: 2, total: TOTAL_PHASES });
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    stableParams.branch,
    stableParams.end_date,
    stableParams.start_date,
    stableParams.listing_type,
    stableParams.status,
    reloadKey,
  ]);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousItems = items.length > 0 || total > 0;

      try {
        if (hasPreviousItems) setItemsRefreshing(true);
        else if (!summary) setLoading(true);

        const itemsResult = await getLmpsDashboardItems(
          { ...stableParams, page, page_size: pageSize },
          controller.signal,
        );
        if (controller.signal.aborted) return;

        setItems(itemsResult.items);
        setTotal(itemsResult.total);
        setCurrentPage(itemsResult.page);
        setPageSize(itemsResult.page_size);
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
        }
      } finally {
        if (!controller.signal.aborted) {
          setItemsRefreshing(false);
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    stableParams.branch,
    stableParams.end_date,
    stableParams.start_date,
    stableParams.listing_type,
    stableParams.status,
    page,
    pageSize,
    reloadKey,
  ]);

  const setPageSize = useCallback((nextPageSize: number) => {
    setPageSizeState(nextPageSize);
    setPage(1);
  }, []);

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
    setPageSize,
    loading,
    refreshing: refreshing || itemsRefreshing,
    requestProgress,
    error,
    reload,
  };
}
