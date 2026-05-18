import { useEffect, useMemo, useRef, useState } from "react";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { fetchStrategicIndicatorsExecutiveSummary } from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { ExecutiveDashboardViewData } from "../../data/types/executiveSummary";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import {
  prefetchStrategicIndicatorsDepartments,
  prefetchStrategicIndicatorsTrends,
} from "./strategicIndicatorsPrefetch";

type UseStrategicIndicatorsExecutiveSummaryParams = {
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsExecutiveSummary({
  departmentId,
  branch,
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

      const cacheKey = buildStrategicIndicatorsCacheKey("executive-summary", {
        competence,
        branch,
        departmentId,
        startDate,
        endDate,
      });
      const cached = getStrategicIndicatorsCachedValue<ExecutiveDashboardViewData>(
        cacheKey,
      );

      beginStrategicIndicatorsLoad({
        cached,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: setData,
        setLoading,
        setRefreshing,
      });

      setError(null);

      try {
        const response = await fetchStrategicIndicatorsExecutiveSummary({
          departmentId,
          branch,
          competence,
          startDate,
          endDate,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        const viewData = adaptExecutiveSummaryToView(response);
        setData(viewData);
        setStrategicIndicatorsCachedValue(cacheKey, viewData);
        hasLoadedOnceRef.current = true;

        prefetchStrategicIndicatorsDepartments({
          competence,
          branch,
          startDate,
          endDate,
          getAccessToken: getAccessTokenRef.current,
        });
        prefetchStrategicIndicatorsTrends({
          competence,
          branch,
          startDate,
          endDate,
          months: 6,
          getAccessToken: getAccessTokenRef.current,
        });
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
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
    };
  }, [departmentId, branch, competence, startDate, endDate]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [departmentId, branch, competence, startDate, endDate]);

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