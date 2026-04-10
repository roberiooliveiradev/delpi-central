import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createAdminDepartmentIndicator,
  deactivateAdminDepartmentIndicator,
  deleteAdminDepartmentIndicator,
  fetchAdminDepartmentIndicators,
  updateAdminDepartmentIndicator,
} from "../../data/api/strategicIndicatorsSettingsApi";
import type {
  AdminDepartmentIndicatorItem,
  CreateAdminDepartmentIndicatorRequest,
  UpdateAdminDepartmentIndicatorRequest,
} from "../../data/types/settings";

type UseStrategicIndicatorsDepartmentIndicatorsParams = {
  departmentId: string | null;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartmentIndicators({
  departmentId,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentIndicatorsParams) {
  const [items, setItems] = useState<AdminDepartmentIndicatorItem[]>([]);
  const [loading, setLoading] = useState(false);
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
      if (!departmentId) {
        setItems([]);
        setLoading(false);
        setRefreshing(false);
        return;
      }

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
        const response = await fetchAdminDepartmentIndicators(
          departmentId,
          getAccessTokenRef.current,
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
            : "Erro inesperado ao carregar indicadores estruturais.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [departmentId]);

  const reload = useCallback(() => loadRef.current(), []);

  useEffect(() => {
    void reload();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [reload]);

  const createIndicator = useCallback(
    async (payload: CreateAdminDepartmentIndicatorRequest) => {
      if (!departmentId) throw new Error("Selecione um departamento.");

      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await createAdminDepartmentIndicator(
          departmentId,
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Indicador estrutural criado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao criar indicador estrutural.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [departmentId],
  );

  const updateIndicator = useCallback(
    async (indicatorId: string, payload: UpdateAdminDepartmentIndicatorRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await updateAdminDepartmentIndicator(
          indicatorId,
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Indicador estrutural atualizado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao atualizar indicador estrutural.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const deactivateIndicator = useCallback(
    async (indicatorId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deactivateAdminDepartmentIndicator(
          indicatorId,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Indicador estrutural desativado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao desativar indicador estrutural.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const removeIndicator = useCallback(
    async (indicatorId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deleteAdminDepartmentIndicator(indicatorId, getAccessTokenRef.current);
        setSuccessMessage("Indicador estrutural excluído com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao excluir indicador estrutural.",
        );
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
      items,
      loading,
      refreshing,
      saving,
      error,
      successMessage,
      reload,
      createIndicator,
      updateIndicator,
      deactivateIndicator,
      removeIndicator,
      clearSuccessMessage,
    }),
    [
      items,
      loading,
      refreshing,
      saving,
      error,
      successMessage,
      reload,
      createIndicator,
      updateIndicator,
      deactivateIndicator,
      removeIndicator,
      clearSuccessMessage,
    ],
  );
}