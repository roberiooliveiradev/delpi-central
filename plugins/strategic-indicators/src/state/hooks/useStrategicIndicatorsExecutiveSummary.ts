import { useEffect, useMemo, useRef, useState } from "react";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { fetchStrategicIndicatorsExecutiveSummary } from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { ExecutiveDashboardViewData } from "../../data/types/executiveSummary";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
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
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

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
      beginSingleRequestProgress(setRequestProgress);

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

        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Resumo executivo",
            route: "/executive-summary",
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
            departmentId: departmentId ?? null,
          }),
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          finishSingleRequestProgress(setRequestProgress, false);
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
      requestProgress,
      error,
      reload: () => loadRef.current(),
    }),
    [data, loading, refreshing, requestProgress, error],
  );
}