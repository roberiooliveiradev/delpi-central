import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchStrategicIndicatorsSettings,
  updateStrategicIndicatorsSettings,
} from "../../data/api/strategicIndicatorsSettingsApi";
import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../../data/types/settings";

type UseStrategicIndicatorsSettingsParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsSettings({
  getAccessToken,
}: UseStrategicIndicatorsSettingsParams) {
  const [data, setData] = useState<StrategicIndicatorsSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
        const response = await fetchStrategicIndicatorsSettings(
          getAccessTokenRef.current,
          controller.signal,
        );

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setData(response);
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, []);

  const reload = useCallback(() => {
    return loadRef.current();
  }, []);

  useEffect(() => {
    void reload();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [reload]);

  const save = useCallback(
    async (payload: StrategicIndicatorsSettingsUpdateRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        const response = await updateStrategicIndicatorsSettings(
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage(response.message);
        await loadRef.current();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro inesperado ao salvar.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const clearSuccessMessage = useCallback(() => {
    setSuccessMessage(null);
  }, []);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      saving,
      error,
      successMessage,
      reload,
      save,
      clearSuccessMessage,
    }),
    [data, loading, refreshing, saving, error, successMessage, reload, save, clearSuccessMessage],
  );
}