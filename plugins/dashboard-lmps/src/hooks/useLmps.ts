import { useCallback, useEffect, useMemo, useState } from "react";
import { listLmps } from "../api/lmpApi";
import type { ListLmpsParams, LmpItem, Page } from "../types/lmp";

type UseLmpsParams = ListLmpsParams & {
  token?: string;
};

type UseLmpsResult = {
  data: Page<LmpItem> | null;
  items: LmpItem[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useLmps(params: UseLmpsParams): UseLmpsResult {
  const [data, setData] = useState<Page<LmpItem> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const stableParams = useMemo(
    () => ({
      date_start: params.date_start,
      date_end: params.date_end,
      page: params.page,
      page_size: params.page_size,
      token: params.token
    }),
    [params.date_start, params.date_end, params.page, params.page_size, params.token]
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

        const result = await listLmps(
          {
            date_start: stableParams.date_start,
            date_end: stableParams.date_end,
            page: stableParams.page,
            page_size: stableParams.page_size
          },
          stableParams.token,
          controller.signal
        );

        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar LMPs");
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
    loading,
    refreshing,
    error,
    reload
  };
}