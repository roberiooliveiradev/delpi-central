import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getLmpsDashboardSummary,
  getLmpsDashboardCharts,
  getLmpsDashboardItems,
  type LmpsDashboardSummary,
  type LmpsDashboardCharts,
  type LmpsDashboardItemsResponse,
} from "../api/lmpApi";
import type { LmpDashboardItem } from "../types/lmp";
import {
  EMPTY_REQUEST_PROGRESS,
  type RequestProgress,
} from "../utils/loadingProgress";

type UseLmpsDashboardParams = {
  date_start?: string;
  date_end?: string;
  branch?: string;
  listing_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
  isActive?: boolean;
};

type UseLmpsDashboardResult = {
  items: LmpDashboardItem[];
  itemsTotal: number;
  summary: LmpsDashboardSummary | null;
  charts: LmpsDashboardCharts | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  reload: () => void;
};

export function useLmpsDashboard(
  params: UseLmpsDashboardParams
): UseLmpsDashboardResult {
  const isActive = params.isActive ?? true;
  const [summary, setSummary] = useState<LmpsDashboardSummary | null>(null);
  const [charts, setCharts] = useState<LmpsDashboardCharts | null>(null);
  const [itemsData, setItemsData] = useState<LmpsDashboardItemsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [itemsRefreshing, setItemsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const filterParams = useMemo(
    () => ({
      date_start: params.date_start,
      date_end: params.date_end,
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

  const itemsParams = useMemo(
    () => ({
      ...filterParams,
      page: params.page,
      page_size: params.page_size,
    }),
    [
      filterParams,
      params.page,
      params.page_size,
    ]
  );

  useEffect(() => {
    if (!isActive) return;

    const controller = new AbortController();

    async function run() {
      const hasPreviousData = summary !== null || charts !== null;

      try {
        setError(null);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const TOTAL_PHASES = 2;
        setRequestProgress({ completed: 0, total: TOTAL_PHASES });

        const summaryResult = await getLmpsDashboardSummary(
          filterParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setSummary(summaryResult);
        setRequestProgress({ completed: 1, total: TOTAL_PHASES });

        const chartsResult = await getLmpsDashboardCharts(
          filterParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setCharts(chartsResult);
        setRequestProgress({ completed: 2, total: TOTAL_PHASES });
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Erro ao carregar dashboard de LMPs"
          );
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
    filterParams.branch,
    filterParams.date_end,
    filterParams.date_start,
    filterParams.listing_type,
    filterParams.status,
    reloadKey,
    isActive,
  ]);

  useEffect(() => {
    if (!isActive) return;

    const controller = new AbortController();

    async function run() {
      const hasPreviousItems = itemsData !== null;

      try {
        if (hasPreviousItems) {
          setItemsRefreshing(true);
        } else if (!summary) {
          setLoading(true);
        }

        const itemsResult = await getLmpsDashboardItems(
          itemsParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setItemsData(itemsResult);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Erro ao carregar itens do dashboard de LMPs"
          );
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
    itemsParams.branch,
    itemsParams.date_end,
    itemsParams.date_start,
    itemsParams.listing_type,
    itemsParams.status,
    itemsParams.page,
    itemsParams.page_size,
    reloadKey,
    isActive,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    items: itemsData?.items ?? [],
    itemsTotal: itemsData?.total ?? 0,
    summary,
    charts,
    loading,
    refreshing: refreshing || itemsRefreshing,
    requestProgress,
    error,
    reload,
  };
}
