import { useEffect, useMemo, useRef, useState } from "react";
import { adaptAlertsToView } from "../../data/adapters/alertsAdapter";
import { fetchStrategicIndicatorsAlerts } from "../../data/api/strategicIndicatorsAlertsApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { AlertsDashboardViewData } from "../../data/types/alerts";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";

type UseStrategicIndicatorsAlertsParams = {
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsAlerts({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsAlertsParams) {
  const [data, setData] = useState<AlertsDashboardViewData | null>(null);
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

      const cacheKey = buildStrategicIndicatorsCacheKey("alerts", {
        competence,
        branch,
        departmentId,
        startDate,
        endDate,
      });
      const cached =
        getStrategicIndicatorsCachedValue<AlertsDashboardViewData>(cacheKey);

      beginStrategicIndicatorsLoad({
        cached,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: setData,
        setLoading,
        setRefreshing,
      });

      setError(null);

      try {
        const response = await fetchStrategicIndicatorsAlerts({
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

        const viewData = adaptAlertsToView(response);
        setData(viewData);
        setStrategicIndicatorsCachedValue(cacheKey, viewData);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar alertas.",
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