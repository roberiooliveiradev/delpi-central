import { useEffect, useMemo, useRef, useState } from "react";
import { adaptTrendsToView } from "../../data/adapters/trendsAdapter";
import { fetchStrategicIndicatorsTrends } from "../../data/api/strategicIndicatorsTrendsApi";
import type { TrendsDashboardViewData } from "../../data/types/trends";

type UseStrategicIndicatorsTrendsParams = {
  competence?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsTrends({
  competence,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsTrendsParams) {
  const [data, setData] = useState<TrendsDashboardViewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    loadRef.current = async () => {
      const requestId = ++requestIdRef.current;

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      if (hasLoadedOnceRef.current) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const response = await fetchStrategicIndicatorsTrends({
          competence,
          months,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setData(adaptTrendsToView(response));
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar tendências.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [competence, months]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [competence, months]);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      error,
      reload: () => loadRef.current(),
    }),
    [data, loading, refreshing, error],
  );
}