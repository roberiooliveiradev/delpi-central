import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  activateStrategicIndicatorGoal,
  bulkCreateStrategicIndicatorGoals,
  createStrategicIndicatorGoal,
  deactivateStrategicIndicatorGoal,
  deleteStrategicIndicatorGoal,
  duplicateStrategicIndicatorGoalsYear,
  fetchStrategicIndicatorGoalHistory,
  fetchStrategicIndicatorGoals,
  fillMissingStrategicIndicatorGoals,
  updateStrategicIndicatorGoal,
} from "../../data/api/strategicIndicatorGoalsApi";
import type {
  BulkCreateStrategicIndicatorGoalsRequest,
  CreateStrategicIndicatorGoalRequest,
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";

type UseStrategicIndicatorGoalsParams = {
  getAccessToken?: () => string | undefined;
  initialGoalYear?: number;
};

export function useStrategicIndicatorGoals({
  getAccessToken,
  initialGoalYear,
}: UseStrategicIndicatorGoalsParams) {
  const [items, setItems] = useState<StrategicIndicatorGoalItem[]>([]);
  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string>("");
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string>("");
  const [selectedGoalYear, setSelectedGoalYear] = useState<number | "">(
    initialGoalYear ?? new Date().getFullYear(),
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyItems, setHistoryItems] = useState<StrategicIndicatorGoalItem[]>(
    [],
  );
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const load = useCallback(async () => {
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
      const response = await fetchStrategicIndicatorGoals(
        getAccessTokenRef.current,
        {
          indicatorId: selectedIndicatorId || undefined,
          departmentId: selectedDepartmentId || undefined,
          goalYear:
            typeof selectedGoalYear === "number" ? selectedGoalYear : undefined,
        },
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
          : "Erro inesperado ao carregar metas analíticas.",
      );
    } finally {
      if (requestId === requestIdRef.current && !controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [selectedIndicatorId, selectedDepartmentId, selectedGoalYear]);

  useEffect(() => {
    void load();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [load]);

  const loadHistory = useCallback(
    async (indicatorId: string, goalYear?: number) => {
      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const response = await fetchStrategicIndicatorGoalHistory(
          indicatorId,
          getAccessTokenRef.current,
          goalYear,
        );
        setHistoryItems(response.items);
      } catch (err) {
        setHistoryError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar o histórico da meta.",
        );
      } finally {
        setHistoryLoading(false);
      }
    },
    [],
  );

  const createGoal = useCallback(
    async (payload: CreateStrategicIndicatorGoalRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await createStrategicIndicatorGoal(payload, getAccessTokenRef.current);
        setSuccessMessage("Meta analítica criada com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao criar a meta analítica.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const updateGoal = useCallback(
    async (goalId: string, payload: UpdateStrategicIndicatorGoalRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await updateStrategicIndicatorGoal(
          goalId,
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Meta analítica atualizada com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao atualizar a meta analítica.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const activateGoal = useCallback(
    async (goalId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await activateStrategicIndicatorGoal(goalId, getAccessTokenRef.current);
        setSuccessMessage("Versão da meta ativada com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao ativar a meta analítica.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const deactivateGoal = useCallback(
    async (goalId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deactivateStrategicIndicatorGoal(
          goalId,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Versão da meta desativada com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao desativar a meta analítica.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const deleteGoal = useCallback(
    async (goalId: string) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deleteStrategicIndicatorGoal(goalId, getAccessTokenRef.current);
        setSuccessMessage("Meta analítica excluída com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao excluir a meta analítica.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const bulkCreateGoals = useCallback(
    async (payload: BulkCreateStrategicIndicatorGoalsRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await bulkCreateStrategicIndicatorGoals(payload, getAccessTokenRef.current);
        setSuccessMessage("Metas criadas em lote com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao criar metas em lote.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const duplicateGoalsYear = useCallback(
    async (payload: DuplicateStrategicIndicatorGoalsYearRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await duplicateStrategicIndicatorGoalsYear(
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Metas duplicadas entre anos com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao duplicar metas entre anos.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const fillMissingGoals = useCallback(
    async (payload: FillMissingStrategicIndicatorGoalsRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await fillMissingStrategicIndicatorGoals(
          payload,
          getAccessTokenRef.current,
        );
        setSuccessMessage("Metas faltantes preenchidas com sucesso.");
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao preencher metas faltantes.",
        );
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const clearSuccessMessage = useCallback(() => {
    setSuccessMessage(null);
  }, []);

  return useMemo(
    () => ({
      items,
      historyItems,
      selectedIndicatorId,
      selectedDepartmentId,
      selectedGoalYear,
      setSelectedIndicatorId,
      setSelectedDepartmentId,
      setSelectedGoalYear,
      loading,
      refreshing,
      saving,
      historyLoading,
      error,
      historyError,
      successMessage,
      reload: load,
      loadHistory,
      createGoal,
      updateGoal,
      activateGoal,
      deactivateGoal,
      deleteGoal,
      bulkCreateGoals,
      duplicateGoalsYear,
      fillMissingGoals,
      clearSuccessMessage,
    }),
    [
      items,
      historyItems,
      selectedIndicatorId,
      selectedDepartmentId,
      selectedGoalYear,
      loading,
      refreshing,
      saving,
      historyLoading,
      error,
      historyError,
      successMessage,
      load,
      loadHistory,
      createGoal,
      updateGoal,
      activateGoal,
      deactivateGoal,
      deleteGoal,
      bulkCreateGoals,
      duplicateGoalsYear,
      fillMissingGoals,
      clearSuccessMessage,
    ],
  );
}