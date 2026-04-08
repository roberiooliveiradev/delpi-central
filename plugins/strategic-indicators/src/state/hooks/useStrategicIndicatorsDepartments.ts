import { useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import type { DepartmentOverviewViewItem } from "../../data/types/departments";

type UseStrategicIndicatorsDepartmentsParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartments({
  getAccessToken,
}: UseStrategicIndicatorsDepartmentsParams) {
  const [items, setItems] = useState<DepartmentOverviewViewItem[]>([]);
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
        const response = await fetchStrategicIndicatorsDepartments(
          getAccessTokenRef.current,
          controller.signal,
        );

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setItems(adaptDepartmentsToView(response));
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar departamentos.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, []);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

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