import { useCallback, useEffect, useState } from "react";

import { formatHrApiError } from "../utils/formatHrApiError";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

type UseHrResourceOptions = {
  enabled?: boolean;
};

type UseHrResourceResult<T> = {
  data: T | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  reload: () => void;
};

export function useHrResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
  options: UseHrResourceOptions = {}
): UseHrResourceResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(options.enabled !== false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );
  const enabled = options.enabled !== false;

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const isRefresh = reloadKey > 0;

    async function run() {
      try {
        setError(null);
        if (isRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        beginSingleRequestProgress(setRequestProgress);
        const result = await fetcher(controller.signal);
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(formatHrApiError(err));
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          finishSingleRequestProgress(setRequestProgress, false);
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, reloadKey, ...deps]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { data, loading, refreshing, requestProgress, error, reload };
}
