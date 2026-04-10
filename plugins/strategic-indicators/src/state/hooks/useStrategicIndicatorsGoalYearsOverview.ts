import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchGoalYearsOverview } from "../../data/api/strategicIndicatorGoalsApi";
import type { GoalYearOverviewItem } from "../../data/types/indicatorGoals";

type UseStrategicIndicatorsGoalYearsOverviewParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsGoalYearsOverview({
  getAccessToken,
}: UseStrategicIndicatorsGoalYearsOverviewParams) {
  const [items, setItems] = useState<GoalYearOverviewItem[]>([]);
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
        const response = await fetchGoalYearsOverview(
          getAccessTokenRef.current,
          controller.signal,
        );

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setItems(response.items);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar visão anual das metas.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, []);

  const reload = useCallback(() => loadRef.current(), []);

  useEffect(() => {
    void reload();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [reload]);

  return useMemo(
    () => ({
      items,
      loading,
      refreshing,
      error,
      reload,
    }),
    [items, loading, refreshing, error, reload],
  );
}