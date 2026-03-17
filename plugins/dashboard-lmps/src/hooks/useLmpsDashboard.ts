import { useCallback, useEffect, useMemo, useState } from "react";
import { getLmpsDashboard, type LmpsDashboardResponse } from "../api/lmpApi";

type UseLmpsDashboardParams = {
  token?: string;
  date_start?: string;
  date_end?: string;
  status?: string;
  page?: number;
  page_size?: number;
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
      status: params.status,
      page: params.page,
      page_size: params.page_size,
      token: params.token
    }),
    [
      params.date_start,
      params.date_end,
      params.status,
      params.page,
      params.page_size,
      params.token
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
            status: stableParams.status,
            page: stableParams.page,
            page_size: stableParams.page_size
          },
          stableParams.token,
          controller.signal
        );

        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar dashboard de LMPs");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    run();

    return () => controller.abort();
  }, [stableParams, reloadKey]);

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
    reload
  };
}