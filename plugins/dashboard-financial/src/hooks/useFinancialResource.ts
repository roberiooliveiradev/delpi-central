import { useCallback, useEffect, useState } from "react";
import { formatFinancialApiError } from "../utils/formatFinancialApiError";

export function useFinancialResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: unknown[]
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = data !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        const result = await fetcher(controller.signal);

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatFinancialApiError(reason));
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
  }, [...deps, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { data, loading, refreshing, error, reload };
}
