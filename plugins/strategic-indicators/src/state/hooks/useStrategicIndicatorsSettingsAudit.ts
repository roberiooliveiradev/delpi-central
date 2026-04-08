import { useEffect, useMemo, useRef, useState } from "react";
import {
  fetchStrategicIndicatorsSettingsAudit,
  type FetchAuditParams,
} from "../../data/api/strategicIndicatorsSettingsAuditApi";
import type { StrategicIndicatorsSettingsAuditItem } from "../../data/types/settingsAudit";

type UseStrategicIndicatorsSettingsAuditParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsSettingsAudit({
  getAccessToken,
}: UseStrategicIndicatorsSettingsAuditParams) {
  const [items, setItems] = useState<StrategicIndicatorsSettingsAuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);
  const lastParamsRef = useRef<FetchAuditParams | undefined>(undefined);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const loadRef = useRef<(params?: FetchAuditParams) => Promise<void>>(async () => {});

  useEffect(() => {
    loadRef.current = async (params?: FetchAuditParams) => {
      lastParamsRef.current = params;

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
        const response = await fetchStrategicIndicatorsSettingsAudit(
          getAccessTokenRef.current,
          params,
          controller.signal,
        );

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setItems(response.items);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar auditoria.",
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
      reload: (params?: FetchAuditParams) =>
        loadRef.current(params ?? lastParamsRef.current),
    }),
    [items, loading, refreshing, error],
  );
}