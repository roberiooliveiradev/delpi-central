import { useCallback, useEffect, useState } from "react";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export function useEngineeringResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: unknown[]
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = data !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        beginSingleRequestProgress(setRequestProgress);
        const result = await fetcher(controller.signal);

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
        }
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
  }, [...deps, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { data, loading, refreshing, requestProgress, error, reload };
}
