import { useCallback, useEffect, useState } from "react";
import { getTransformaSummary } from "../api/engineeringApi";
import type { EngineeringFilterParams, TransformaSummary } from "../types/engineering";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";

export function useEngineeringDashboard(apiParams: EngineeringFilterParams) {
  const [summary, setSummary] = useState<TransformaSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = summary !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        const result = await getTransformaSummary(apiParams, controller.signal);

        if (!controller.signal.aborted) {
          setSummary(result);
        }
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
  }, [apiParams.branch, apiParams.end_date, apiParams.filial_id, apiParams.start_date, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { summary, loading, refreshing, error, reload };
}
