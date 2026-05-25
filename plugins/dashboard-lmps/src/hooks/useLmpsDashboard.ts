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
};

type UseLmpsDashboardResult = {
  items: LmpDashboardItem[];
  itemsTotal: number;
  summary: LmpsDashboardSummary | null;
  charts: LmpsDashboardCharts | null;
  loading: boolean;
  itemsLoading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  reload: () => void;
};

export function useLmpsDashboard(
  params: UseLmpsDashboardParams
): UseLmpsDashboardResult {
  const [summary, setSummary] = useState<LmpsDashboardSummary | null>(null);
  const [charts, setCharts] = useState<LmpsDashboardCharts | null>(null);
  const [itemsData, setItemsData] = useState<LmpsDashboardItemsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [itemsLoading, setItemsLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const stableParams = useMemo(
    () => ({
      date_start: params.date_start,
      date_end: params.date_end,
      branch: params.branch,
      listing_type: params.listing_type,
      status: params.status,
      page: params.page,
      page_size: params.page_size,
    }),
    [
      params.date_start,
      params.date_end,
      params.branch,
      params.listing_type,
      params.status,
      params.page,
      params.page_size,
    ]
  );

  useEffect(() => {
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
          stableParams,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setItemsData(itemsResult);
        setRequestProgress({ completed: 3, total: TOTAL_PHASES });
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Erro ao carregar dashboard de LMPs"
          );
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
    stableParams.page,
    stableParams.page_size,
    reloadKey,
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
    itemsLoading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
