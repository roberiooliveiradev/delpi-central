import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import {
  fetchStrategicIndicatorsExecutiveSummary,
  type FetchStrategicIndicatorsExecutiveSummaryParams,
} from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import type { ExecutiveDashboardViewData } from "../../data/types/executiveSummary";

type UseStrategicIndicatorsExecutiveSummaryParams = {
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsExecutiveSummary({
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsExecutiveSummaryParams) {
  const [data, setData] = useState<ExecutiveDashboardViewData | null>(null);
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

    const hasPreviousData = data !== null;

    if (hasPreviousData) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError(null);

    try {
      const response = await fetchStrategicIndicatorsExecutiveSummary({
        competence,
        startDate,
        endDate,
        getAccessToken,
        signal: controller.signal,
      } satisfies FetchStrategicIndicatorsExecutiveSummaryParams);

      if (requestId !== requestIdRef.current) {
        return;
      }

      setData(adaptExecutiveSummaryToView(response));
    } catch (err) {
      if (controller.signal.aborted || requestId !== requestIdRef.current) {
        return;
      }

      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar resumo executivo.",
      );
    } finally {
      if (requestId === requestIdRef.current && !controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [competence, startDate, endDate, getAccessToken, data]);

  useEffect(() => {
    void load();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [load]);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      error,
      reload: load,
    }),
    [data, loading, refreshing, error, load],
  );
}