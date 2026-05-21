import { useEffect, useMemo, useRef, useState } from "react";
import { adaptTrendsToView } from "../../data/adapters/trendsAdapter";
import { fetchStrategicIndicatorsTrends } from "../../data/api/strategicIndicatorsTrendsApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import type { TrendsDashboardViewData } from "../../data/types/trends";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";

type UseStrategicIndicatorsTrendsParams = {
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsTrends({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsTrendsParams) {
  const [data, setData] = useState<TrendsDashboardViewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(EMPTY_REQUEST_PROGRESS);
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);

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

      const cacheKey = buildStrategicIndicatorsCacheKey("trends", {
        competence,
        branch,
        departmentId,
        startDate,
        endDate,
        months,
      });
      const cached =
        getStrategicIndicatorsCachedValue<TrendsDashboardViewData>(cacheKey);

      beginStrategicIndicatorsLoad({
        cached,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: setData,
        setLoading,
        setRefreshing,
      });

      setError(null);
      beginSingleRequestProgress(setRequestProgress);

      try {
        const response = await fetchStrategicIndicatorsTrends({
          departmentId,
          branch,
          competence,
          startDate,
          endDate,
          months,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        const viewData = adaptTrendsToView(response);
        setData(viewData);
        setStrategicIndicatorsCachedValue(cacheKey, viewData);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Tendências",
            route: "/trends",
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
            departmentId: departmentId ?? null,
          }),
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          finishSingleRequestProgress(setRequestProgress, controller.signal.aborted);
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [departmentId, branch, competence, startDate, endDate, months]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [departmentId, branch, competence, startDate, endDate, months]);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      requestProgress,
      error,
      reload: () => loadRef.current(),
    }),
    [data, loading, refreshing, requestProgress, error],
  );
}