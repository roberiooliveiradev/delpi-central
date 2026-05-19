import { useCallback, useEffect, useMemo, useState } from "react";
import { getLmpsDashboard, type LmpsDashboardResponse } from "../api/lmpApi";

type UseLmpsDashboardParams = {
  date_start?: string;
  date_end?: string;
  branch?: string;
  listing_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
  autoRefreshMs?: number;
};

type UseLmpsDashboardResult = {
  data: LmpsDashboardResponse | null;
  items: LmpsDashboardResponse["items"];
  summary: LmpsDashboardResponse["summary"] | null;
  charts: LmpsDashboardResponse["charts"] | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useLmpsDashboard(
  params: UseLmpsDashboardParams
): UseLmpsDashboardResult {
  const [data, setData] = useState<LmpsDashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

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
      const hasPreviousData = Boolean(data);

      try {
        setError(null);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const result = await getLmpsDashboard(
          {
            date_start: stableParams.date_start,
            date_end: stableParams.date_end,
            branch: stableParams.branch,
            listing_type: stableParams.listing_type,
            status: stableParams.status,
            page: stableParams.page,
            page_size: stableParams.page_size,
          },
          controller.signal
        );

        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar dashboard de LMPs"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [stableParams, reloadKey]);

  useEffect(() => {
    if (!params.autoRefreshMs || params.autoRefreshMs <= 0) return;

    const intervalId = window.setInterval(() => {
      if (document.visibilityState !== "visible") return;

      setReloadKey((prev) => prev + 1);
    }, params.autoRefreshMs);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [params.autoRefreshMs]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    data,
    items: data?.items ?? [],
    summary: data?.summary ?? null,
    charts: data?.charts ?? null,
    loading,
    refreshing,
    error,
    reload,
  };
}