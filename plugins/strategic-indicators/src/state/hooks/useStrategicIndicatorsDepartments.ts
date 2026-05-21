import { useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { DepartmentOverviewViewItem } from "../../data/types/departments";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";

type UseStrategicIndicatorsDepartmentsParams = {
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartments({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentsParams) {
  const [items, setItems] = useState<DepartmentOverviewViewItem[]>([]);
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

      const cacheKey = buildStrategicIndicatorsCacheKey("departments", {
        competence,
        branch,
        departmentId,
        startDate,
        endDate,
      });
      const cached = getStrategicIndicatorsCachedValue<DepartmentOverviewViewItem[]>(
        cacheKey,
      );

      beginStrategicIndicatorsLoad({
        cached,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: setItems,
        setLoading,
        setRefreshing,
      });

      setError(null);

      try {
        const response = await fetchStrategicIndicatorsDepartments({
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

        const viewItems = adaptDepartmentsToView(response);
        setItems(viewItems);
        setStrategicIndicatorsCachedValue(cacheKey, viewItems);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Departamentos",
            route: "/departments",
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
      loading,
      refreshing,
      error,
      reload: () => loadRef.current(),
    }),
    [items, loading, refreshing, error],
  );
}