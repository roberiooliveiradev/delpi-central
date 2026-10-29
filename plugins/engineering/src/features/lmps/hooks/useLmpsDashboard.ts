import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getLmpsDashboardItems,
  getLmpGoalContext,
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
  start_date?: string;
  end_date?: string;
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

/** E-LMP-01 consolida itens + KPIs realizados + agregados de gráfico num
 * único contrato (`GET /v1/lmps`). O legado usava 3 endpoints separados
 * na api-delpi; aqui uma chamada alimenta os três estados. */
export function useLmpsDashboard(
  params: UseLmpsDashboardParams
): UseLmpsDashboardResult {
  const isActive = params.isActive ?? true;
  const [summary, setSummary] = useState<LmpsDashboardSummary | null>(null);
  const [charts, setCharts] = useState<LmpsDashboardCharts | null>(null);
  const [itemsData, setItemsData] = useState<LmpsDashboardItemsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const requestParams = useMemo(
    () => ({
      start_date: params.start_date,
      end_date: params.end_date,
      branch: params.branch,
      listing_type: params.listing_type,
      status: params.status,
      page: params.page,
      page_size: params.page_size,
    }),
    [
      params.start_date,
      params.end_date,
      params.branch,
      params.listing_type,
      params.status,
      params.page,
      params.page_size,
    ]
  );

  useEffect(() => {
    if (!isActive) return;

    const controller = new AbortController();

    async function run() {
      const hasPreviousData = summary !== null || itemsData !== null;

      try {
        setError(null);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        setRequestProgress({ completed: 0, total: 2 });

        // Metas pertencem a Strategic Indicators — chegam pelo adapter
        // delegado /v1/lmps/goal-context e são mescladas ao summary
        // realizado (campos disjuntos). Unavailable/forbidden → null,
        // sem meta inventada.
        const [result, goalContext] = await Promise.all([
          getLmpsDashboardItems(requestParams, controller.signal),
          getLmpGoalContext(requestParams, controller.signal),
        ]);
        if (controller.signal.aborted) return;

        setItemsData(result);
        if (result.summary) {
          setSummary({ ...goalContext, ...result.summary });
        }
        if (result.charts) setCharts(result.charts);
        setRequestProgress({ completed: 2, total: 2 });
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
    requestParams.branch,
    requestParams.end_date,
    requestParams.start_date,
    requestParams.listing_type,
    requestParams.status,
    requestParams.page,
    requestParams.page_size,
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
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
