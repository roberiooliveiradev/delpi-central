import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createAdminDepartment,
  deactivateAdminDepartment,
  deleteAdminDepartment,
  fetchAdminDepartments,
  updateAdminDepartment,
} from "../../data/api/strategicIndicatorsSettingsApi";
import type {
  AdminDepartmentItem,
  CreateAdminDepartmentRequest,
  UpdateAdminDepartmentRequest,
} from "../../data/types/settings";

type UseStrategicIndicatorsAdminDepartmentsParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsAdminDepartments({
  getAccessToken,
}: UseStrategicIndicatorsAdminDepartmentsParams) {
  const [items, setItems] = useState<AdminDepartmentItem[]>([]);
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
        const response = await fetchAdminDepartments(
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
            : "Erro inesperado ao carregar departamentos administrativos.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, []);

  const reload = useCallback(() => loadRef.current(), []);

  useEffect(() => {
    void reload();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [reload]);

  const createDepartment = useCallback(
    async (payload: CreateAdminDepartmentRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await createAdminDepartment(payload, getAccessTokenRef.current);
        setSuccessMessage("Departamento criado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro inesperado ao criar departamento.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const updateDepartment = useCallback(
    async (departmentId: string, payload: UpdateAdminDepartmentRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await updateAdminDepartment(
          departmentId,
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Departamento atualizado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro inesperado ao atualizar departamento.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const deactivateDepartment = useCallback(
    async (departmentId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deactivateAdminDepartment(departmentId, getAccessTokenRef.current);
        setSuccessMessage("Departamento desativado com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro inesperado ao desativar departamento.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const removeDepartment = useCallback(
    async (departmentId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deleteAdminDepartment(departmentId, getAccessTokenRef.current);
        setSuccessMessage("Departamento excluído com sucesso.");
        await loadRef.current();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro inesperado ao excluir departamento.",
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
      createDepartment,
      updateDepartment,
      deactivateDepartment,
      removeDepartment,
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
      createDepartment,
      updateDepartment,
      deactivateDepartment,
      removeDepartment,
      clearSuccessMessage,
    ],
  );
}