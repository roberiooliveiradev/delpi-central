import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import {
  fetchStrategicIndicators,
  type FetchStrategicIndicatorsParams,
} from "../../data/api/strategicIndicatorsApi";
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

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const hasPreviousData = items.length > 0;

    if (hasPreviousData) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError(null);

    try {
      const params: FetchStrategicIndicatorsParams = {
        departmentId,
        startDate,
        endDate,
        getAccessToken,
        signal: controller.signal,
      };

      const response = await fetchStrategicIndicators(params);

      if (requestId !== requestIdRef.current) {
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
    } catch (err) {
      if (controller.signal.aborted || requestId !== requestIdRef.current) {
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
  }, [departmentId, startDate, endDate, getAccessToken, items.length]);

  useEffect(() => {
    void load();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [load]);

  return useMemo(
    () => ({
      items,
      fetchErrors,
      partialSuccess,
      loading,
      refreshing,
      error,
      reload: load,
    }),
    [items, fetchErrors, partialSuccess, loading, refreshing, error, load],
  );
}