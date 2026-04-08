import { useEffect, useMemo, useRef, useState } from "react";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import { fetchStrategicIndicators } from "../../data/api/strategicIndicatorsApi";
import type {
  IndicatorFetchErrorViewItem,
  IndicatorViewItem,
} from "../../data/types/indicators";

type UseStrategicIndicatorsParams = {
  departmentId?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicators({
  departmentId,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsParams) {
  const [items, setItems] = useState<IndicatorViewItem[]>([]);
  const [fetchErrors, setFetchErrors] = useState<IndicatorFetchErrorViewItem[]>([]);
  const [partialSuccess, setPartialSuccess] = useState(false);
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
        const response = await fetchStrategicIndicators({
          departmentId,
          startDate,
          endDate,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setItems(adaptIndicatorsToView(response));
        setFetchErrors(
          (response.errors ?? []).map((item) => ({
            departmentId: item.department_id,
            source: item.source,
            message: item.message,
          })),
        );
        setPartialSuccess(Boolean(response.partial_success));
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar indicadores.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [departmentId, startDate, endDate]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [departmentId, startDate, endDate]);

  return useMemo(
    () => ({
      items,
      fetchErrors,
      partialSuccess,
      loading,
      refreshing,
      error,
      reload: () => loadRef.current(),
    }),
    [items, fetchErrors, partialSuccess, loading, refreshing, error],
  );
}