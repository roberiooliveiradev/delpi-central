import { useEffect, useMemo, useRef, useState } from "react";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import { fetchStrategicIndicators } from "../../data/api/strategicIndicatorsApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type {
  IndicatorFetchErrorViewItem,
  IndicatorViewItem,
} from "../../data/types/indicators";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";

type IndicatorsQueryState = {
  items: IndicatorViewItem[];
  fetchErrors: IndicatorFetchErrorViewItem[];
  partialSuccess: boolean;
};

type UseStrategicIndicatorsParams = {
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicators({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsParams) {
  const [items, setItems] = useState<IndicatorViewItem[]>([]);
  const [fetchErrors, setFetchErrors] = useState<IndicatorFetchErrorViewItem[]>([]);
  const [partialSuccess, setPartialSuccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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

      const cacheKey = buildStrategicIndicatorsCacheKey("indicators", {
        competence,
        branch,
        departmentId,
        startDate,
        endDate,
      });
      const cached =
        getStrategicIndicatorsCachedValue<IndicatorsQueryState>(cacheKey);

      beginStrategicIndicatorsLoad({
        cached: cached
          ? {
              items: cached.items,
              fetchErrors: cached.fetchErrors,
              partialSuccess: cached.partialSuccess,
            }
          : null,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: (value) => {
          setItems(value.items);
          setFetchErrors(value.fetchErrors);
          setPartialSuccess(value.partialSuccess);
        },
        setLoading,
        setRefreshing,
      });

      setError(null);

      try {
        const response = await fetchStrategicIndicators({
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

        const nextState: IndicatorsQueryState = {
          items: adaptIndicatorsToView(response),
          fetchErrors: (response.errors ?? []).map((item) => ({
            departmentId: item.department_id,
            source: item.source,
            message: item.message,
          })),
          partialSuccess: Boolean(response.partial_success),
        };
        setItems(nextState.items);
        setFetchErrors(nextState.fetchErrors);
        setPartialSuccess(nextState.partialSuccess);
        setStrategicIndicatorsCachedValue(cacheKey, nextState);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Lista de indicadores",
            route: "/indicators",
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
            departmentId: departmentId ?? null,
          }),
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